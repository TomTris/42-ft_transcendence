from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import json
from .models import get_invites, Invite
from .serializers import InviteSerializer
from users.models import User, Friendship
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
import threading
import time
import asyncio


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
        self.send_to_all(1)

    def disconnecting(self):
        id = self.user.id
        def checking(id):
            time.sleep(10)
            if User.objects.get(id=id).online_check == False:
                self.user.is_online = False
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
                self.send_to_two(invite.send_to.id, invite.sender.id, 2)

        self.send_to_all()
    
    def invite_message2(self, event):
        id1 = event['id1']
        id2 = event['id2']
        update = event['update']
        if self.user.id == id1 or self.user.id == id2:
            messages = Invite.objects.filter(send_to=self.user).order_by('-id')
            invite_data = self.serialize_invites(messages)
            response_data = {
                'type': 'invites',
                'invites': invite_data,
                'update': update,
            }
            self.send(text_data=json.dumps(response_data))


    def send_to_two(self, id1, id2, update):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'invite_message2',
                'update':update,
                'id1':id1,
                'id2':id2
            }
        )


    def send_to_all(self, id1, id2, update=0):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'invite_message',
                'update':update,
            }
        )


    def invite_message(self, event={'update':0}):
        update = event['update']
        messages = Invite.objects.filter(send_to=self.user).order_by('-id')
        invite_data = self.serialize_invites(messages)
        # print(invite_data)
        response_data = {
            'type': 'invites',
            'invites': invite_data,
            # 'update': update,
        }
        self.send(text_data=json.dumps(response_data))

    def invite_accept(self, event):
        id1 = event['id1']
        id2 = event['id2']
        link = event['link']
        if self.user.id == id1 or self.user.id == id2:
            response_data = {
                'type': 'redirect',
                'link': link,
                'update':0,
            }
            self.send(text_data=json.dumps(response_data))

    def serialize_invites(self, invites):
        serializer = InviteSerializer(invites, many=True)
        return serializer.data