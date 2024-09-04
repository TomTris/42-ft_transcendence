from django.db import models
from django.conf import settings
from django.db.models import Q

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
    messages = Message.objects.filter(Q(send_to=user.username) | Q(send_to=None) | Q(sender=user))
    not_blocked = messages.exclude(sender__in=blocked).order_by('-id')[:50][::-1]
    for i in not_blocked:
        print(i.sender, i.send_to, i.content)
    return not_blocked