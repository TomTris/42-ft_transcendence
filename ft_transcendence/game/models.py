from django.db import models
from django.conf import settings
import time

class GameSession(models.Model):
    player1 = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='game_player1', null=True, on_delete=models.SET_NULL)
    player2 = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='game_player2', null=True, on_delete=models.SET_NULL)
    score1 = models.IntegerField(default=0)
    score2 = models.IntegerField(default=0)
    # disc1 = models.B
    rank_change1 = models.IntegerField(default=0)
    rank_change2 = models.IntegerField(default=0)
    game_state = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_full(self):
        return self.player1 and self.player2

    def add_player(self, user):
        if not self.player1:
            self.player1 = user
        elif not self.player2:
            self.player2 = user
        else:
            raise ValueError("Game session is already full")
        self.save()

    def disconnect(self, user):
        pass




    def save(self, *args, **kwargs):
        if self.is_full() and not self.is_active:
            self.is_active = True
        super().save(*args, **kwargs)