from rest_framework import serializers
from .models import Invite
from users.models import MyUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'username', 'avatar']



class InviteSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    send_to = UserSerializer()
    class Meta:
        model = Invite
        fields = ['id', 'sender', 'send_to', 'invite_type']