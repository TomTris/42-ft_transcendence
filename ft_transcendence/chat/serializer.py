from rest_framework import serializers
from .models import Message

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['sender', 'send_to', 'content']