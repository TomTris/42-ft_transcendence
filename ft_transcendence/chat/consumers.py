from channels.generic.websocket import WebsocketConsumer
import json
from .models import get_messages, BlockList, Message
from users.models import User
from .serializer import ChatMessageSerializer
from asgiref.sync import async_to_sync
from pages.models import Invite


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.group_name = 'chat'
        async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
        self.accept()
        self.send_to_all()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )


    def clean_message(self, message):
        message = message.lstrip()
        if not message:
            return 0, 'a', 'a'

        if message.startswith('to:') or message.startswith('To:'):
            message = message[3:]
            words = message.split()
            if len(words) < 2:
                return 0, 'a', 'a'

            reciver = words[0]
            message = message[len(reciver):]
            message = message.lstrip()

            user = User.objects.filter(username=reciver).first()
            if not user:
                return 0, 'a', 'a'
            return 1, user, message
        else:
            return 1, None, message


    def receive(self, text_data):
        data = json.loads(text_data)
        print(data)
        if data['type'] == 'message':
            is_valid, reciver, content = self.clean_message(data['content'])
            if is_valid:
                Message.objects.create(
                    sender=self.user,
                    send_to=reciver,
                    content=content
                )
                if reciver is not None:
                    self.send_to_two(self.user.id, reciver.id)
                else:
                    self.send_to_all()

        if data['type'] == 'block':
            blocker = self.user
            blocked = User.objects.filter(id=data['id']).first()
            if blocked is not None:
                BlockList.objects.create(
                    blocker=blocker,
                    blocked=blocked
                )
                self.send_to_one(self.user.id)
        
        if data['type'] == 'play':
            sender = self.user
            send_to = User.objects.filter(id=data['id']).first()
            if send_to is not None:
                Invite.objects.filter(sender=sender, send_to=send_to, invite_type=2).delete()
                Invite.objects.create(
                    sender=sender,
                    send_to=send_to,
                    invite_type=2
                )

                async_to_sync(self.channel_layer.group_send)(
                    'invite',
                    {
                        'type': 'invite_message',
                        'id1':self.user.id,
                        'id2':data['id'],
                        'update':2,
                    }
                )

        if data['type'] == 'friend':
            sender = self.user
            send_to = User.objects.filter(id=data['id']).first()
            if send_to is not None:
                Invite.objects.filter(sender=sender, send_to=send_to, invite_type=1).delete()
                Invite.objects.create(
                    sender=sender,
                    send_to=send_to,
                    invite_type=1
                )
                async_to_sync(self.channel_layer.group_send)(
                    'invite',
                    {
                        'type': 'invite_message',
                        'id1':self.user.id,
                        'id2':data['id'],
                        'update':2,
                    }
                )



    def sending_to_one(self, event):
        id = event['id']
        if self.user.id == id:
            messages = get_messages(self.user)
            serializer = ChatMessageSerializer(messages, many=True)
            message_data = serializer.data
            response_data = {
                'messages': message_data,
                'current_user': self.user.username,
            }
            self.send(text_data=json.dumps(response_data))


    def sending_to_two(self, event):
        id1 = event['id1']
        id2 = event['id2']
        if self.user.id == id1 or self.user.id == id2:
            messages = get_messages(self.user)
            serializer = ChatMessageSerializer(messages, many=True)
            message_data = serializer.data
            response_data = {
                'messages': message_data,
                'current_user': self.user.username,
            }
            self.send(text_data=json.dumps(response_data))

    def sending_to_four(self, event):
        id1 = event['id1']
        id2 = event['id2']
        id3 = event['id3']
        id4 = event['id4']
        if self.user.id in [id1, id2, id3, id4]:
            messages = get_messages(self.user)
            serializer = ChatMessageSerializer(messages, many=True)
            message_data = serializer.data
            response_data = {
                'messages': message_data,
                'current_user': self.user.username,
            }
            self.send(text_data=json.dumps(response_data))


    def send_to_two(self, id1, id2):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'sending_to_two',
                'id1':id1,
                'id2':id2
            }
        )


    def send_to_one(self, id):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'sending_to_one',
                'id':id
            }
        )

    def send_to_all(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'chat_message',
            }
        )


    def chat_message(self, event):
        messages = get_messages(self.user)
        serializer = ChatMessageSerializer(messages, many=True)
        message_data = serializer.data
        response_data = {
            'messages': message_data,
            'current_user': self.user.username,
        }
        self.send(text_data=json.dumps(response_data))