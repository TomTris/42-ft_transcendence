from django.db import models
from django.conf import settings
from django.db.models import Q
from itertools import chain


# Create your models here.


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender_message', null=True, on_delete=models.CASCADE)
    send_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reciver_message', null=True, on_delete=models.CASCADE)
    content = models.CharField(max_length=200)
    game_id = models.IntegerField(null=True)


class BlockList(models.Model):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocker', null=True, on_delete=models.SET_NULL)
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked', null=True, on_delete=models.SET_NULL)


def get_messages(user):
    blocked = BlockList.objects.filter(blocker=user).values_list('blocked', flat=True)
    messages = Message.objects.filter(Q(send_to=user) | Q(send_to=None) | Q(sender=user)).exclude(sender__isnull=True).exclude(sender__in=blocked)
    system_messages = Message.objects.filter(sender=None, send_to=user)
    combined_messages = list(chain(messages[:50], system_messages))
    return combined_messages