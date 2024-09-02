from rest_framework import serializers
from .models import Invite
from users.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']



class InviteSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    send_to = UserSerializer()
    class Meta:
        model = Invite
        fields = ['id', 'sender', 'send_to', 'invite_type']