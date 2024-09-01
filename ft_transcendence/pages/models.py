from django.db import models
from django.conf import settings
from django.db.models import Q
from chat.models import BlockList

# Create your models here.
class Invite(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender_invite', null=True, on_delete=models.SET_NULL)
    send_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='send_to', null=True, on_delete=models.SET_NULL)
    invite_type=models.IntegerField()


def get_invites(user):
    Invite.objects.filter(send_to=user)