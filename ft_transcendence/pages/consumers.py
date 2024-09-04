from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from channels.generic.websocket import WebsocketConsumer
import json
from .models import get_invites, Invite
from .serializers import InviteSerializer
from users.models import User, Friendship
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
import threading
import time
import asyncio

from rest_framework_simplejwt.authentication import JWTAuthentication

class InviteConsumer(WebsocketConsumer):

    def connect(self):
        self.user = self.scope['user']
        self.group_name = 'invite'
        async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
        self.accept()
        self.user.is_online = True
        self.user.online_check = True
        self.user.save()
        self.send_to_all()

    def disconnecting(self):
        id = self.user.id
        def checking(id):
            time.sleep(10)
            if User.objects.get(id=id).online_check == False:
                self.user.is_online = False
                print('disconect')
                self.user.save()
        
        self.periodic_task = threading.Thread(target=checking, daemon=True)
        self.periodic_task.start(id)



    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )
        self.user.online_check = False
        self.disconnecting()


    def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'friendship':
            invite = Invite.objects.filter(id=data['id']).first()
            if invite is not None:
                if data['result'] == 'accept':
                    Friendship.objects.create(person1=invite.sender, person2=invite.send_to)
                invite.delete()


        self.send_to_all()
        

    def send_to_all(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'invite_message',
            }
        )


    def invite_message(self, event):
        print("invite_message called")
        print(self.user)
        print("invite_message called")
        user = self.user.user if hasattr(self.user, 'user') else self.user
        print(user.is_verified)
        print("invite_message called")
        messages = Invite.objects.filter(send_to=self.user)[::-1]
        print("invite_message called done")
        print(messages)
        serializer = InviteSerializer(messages, many=True)
        invite_data = serializer.data
        response_data = {
            'type': 'invites',
            'invites': invite_data,
        }
        self.send(text_data=json.dumps(response_data))

    def invite_accept(self, event):
        id1 = event['id1']
        id2 = event['id2']
        link = event['link']
        print(self.user.id, id1, id2)
        if self.user.id == id1 or self.user.id == id2:
            print('inside')
            response_data = {
                'type': 'redirect',
                'link': link,
            }
            self.send(text_data=json.dumps(response_data))

    def serialize_invites(self, invites):
        serializer = InviteSerializer(invites, many=True)
        return serializer.data