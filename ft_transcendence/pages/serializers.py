from rest_framework import serializers
from .models import Invite
from users.models import User
from chat.models import BlockList

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


class BlockListSerializer(serializers.ModelSerializer):
    blocked = UserSerializer()
    class Meta:
        model = BlockList
        fields = ['id', 'blocked']

