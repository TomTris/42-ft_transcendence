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
from game.models import GameSession
from channels.layers import get_channel_layer

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
        self.send_to_all(-1, -1, 1)

    def disconnecting(self):
        id = self.user.id
        def checking(id):
            time.sleep(5)
            self.user = User.objects.get(id=self.user.id)
            if self.user.online_check == False:
                self.user.is_online = False
                self.user.save()
                self.send_to_all(-1, -1, 1)

        
        self.periodic_task = threading.Thread(target=checking, args=(id,), daemon=True)
        self.periodic_task.start()



    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )
        self.user.online_check = False
        self.user = User.objects.get(id=self.user.id)
        self.user.save()
        self.disconnecting()


    def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'friendship':
            invite = Invite.objects.filter(id=data['id']).first()
            Invite.objects.filter(sender=invite.send_to, send_to=invite.sender, invite_type=invite.invite_type).delete()
            if invite is not None:
                if invite.invite_type == 1:
                    if data['result'] == 'accept':
                        Friendship.objects.create(person1=invite.sender, person2=invite.send_to)
                    invite.delete()
                    self.send_to_all(invite.send_to.id, invite.sender.id, 2)
                else:
                    sender = invite.sender
                    send_to = invite.send_to
                    if data['result'] == 'accept':
                        if sender.is_playing == False and send_to.is_playing == False and sender.is_online and sender.online_check:
                            game = GameSession.objects.create(
                                player1=sender,
                                player2=send_to,
                            )
                            game.init_game_state()
                            channel_layer = get_channel_layer()
                            link = f'/game/{game.id}/'
                            async_to_sync(channel_layer.group_send)(
                                'invite',
                                {
                                    'type': 'invite_accept',
                                    'id1': sender.id,
                                    'id2': send_to.id,
                                    'link': link
                                }
                            )
                            async_to_sync(channel_layer.group_send)(
                                'invite',
                                {
                                    'type':'invite_message',
                                    'id1':sender.id,
                                    'id2':send_to.id,
                                    'update':0,
                                }
                            )
                            invite.delete()
                    else:
                        self.send_to_all(sender.id, send_to.id, 2)
                        invite.delete()
        

    def send_to_all(self, id1, id2, update):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'invite_message',
                'id1':id1,
                'id2':id2,
                'update':update,
            }
        )


    def invite_message(self, event):
        user = self.user.user if hasattr(self.user, 'user') else self.user
        id1 = event['id1']
        id2 = event['id2']
        update = event['update']

        if user.id == id1 or user.id == id2 or id1 == -1:
            messages = Invite.objects.filter(send_to=self.user)[::-1]
            serializer = InviteSerializer(messages, many=True)
            invite_data = serializer.data
            response_data = {
                'type': 'invites',
                'invites': invite_data,
                'update':update
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
            }
            self.send(text_data=json.dumps(response_data))

    def serialize_invites(self, invites):
        serializer = InviteSerializer(invites, many=True)
        return serializer.data