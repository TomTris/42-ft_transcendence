from channels.generic.websocket import WebsocketConsumer
import json
from .models import get_messages, BlockList, Message
from users.models import User
from .serializer import ChatMessageSerializer
from asgiref.sync import async_to_sync

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
            if reciver == 'all':
                return 1, None, message
            user = User.objects.filter(username=reciver).first()
            if not user:
                return 0, 'a', 'a'
            return 1, user, message
        else:
            return 1, None, message


    def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'message':
            is_valid, reciver, content = self.clean_message(data['content'])
            print(f"is_valid={is_valid}, reciver={reciver}, content={content}")
            if is_valid:
                Message.objects.create(
                    sender=self.user,
                    send_to=reciver,
                    content=content
                )
                self.send_to_all()
        if data['type'] == 'block':
            pass


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