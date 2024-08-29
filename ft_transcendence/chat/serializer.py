from rest_framework import serializers
from .models import Message
from users.models import MyUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'username', 'avatar']



class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    class Meta:
        model = Message
        fields = ['sender', 'send_to', 'content', 'game_id']