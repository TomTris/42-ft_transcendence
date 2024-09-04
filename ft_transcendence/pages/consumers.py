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


class InviteConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        self.group_name = 'invite'
        await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
        await self.accept()
        await self.send_to_all()
        await self.set_user_online_status(True)

    # def disconnecting(self):
    #     id = self.user.id
    #     def checking():
    #         nonlocal id
    #         time.sleep(10)
    #         print('disconect')
    #         if User.objects.get(id=id).online_check == False:
    #             self.user.is_online = False
    #             self.user.save()
        
    #     self.periodic_task = threading.Thread(target=checking, daemon=True)
    #     self.periodic_task.start()

    async def disconnecting(self):
        await asyncio.sleep(10)  # Async sleep to avoid blocking the event loop
        if not await self.get_user_online_check():
            await self.set_user_is_online(False)


    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        await self.set_user_status(False)
        await self.disconnecting()


    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'friendship':
            invite = await database_sync_to_async(Invite.objects.filter(id=data['id']).first())
            if invite is not None:
                if data['result'] == 'accept':
                    await database_sync_to_async(Friendship.objects.create(person1=invite.sender, person2=invite.send_to))
                invite.delete()


        self.send_to_all()
        

    async def send_to_all(self):
        self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'invite_message',
            }
        )


    async def invite_message(self, event):

        messages = await database_sync_to_async(Invite.objects.filter(send_to=self.user)[::-1])
        serializer = InviteSerializer(messages, many=True)
        invite_data = serializer.data
    
        response_data = {
            'invites': invite_data,
        }
        await self.send(text_data=json.dumps(response_data))

    @database_sync_to_async
    def set_user_is_online(self, status):
        self.user.is_online = status
        self.user.save()

    @database_sync_to_async
    def set_user_online_status(self, status):
        self.user.online_check = status
        self.user.is_online = status
        self.user.save()
        print(self.user.username, self.user.is_online)

    @database_sync_to_async
    def get_user_online_check(self):
        return self.user.online_check
    
    @database_sync_to_async
    def set_user_status(self, status):
        self.user.online_check = status
        self.user.save()