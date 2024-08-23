from django.db import models
from django.conf import settings
import time
import random
import math
from django.core.cache import cache

width = 800
height = 400
pheight = 80
pwidth = 15
distance = 40
radius = 10


class GameSession(models.Model):
    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='game_player1', null=True, on_delete=models.SET_NULL)
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='game_player2', null=True, on_delete=models.SET_NULL)
    score1 = models.IntegerField(default=0)
    score2 = models.IntegerField(default=0)
    rank_change1 = models.IntegerField(default=0)
    rank_change2 = models.IntegerField(default=0)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='winner', null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_cache_key(self):
        return f'game_session_game_state_{self.id}'

    def set_game_state(self, game_state):
        cache.set(self.get_cache_key(), game_state, timeout=None)  # Timeout can be set according to your needs

    def get_game_state(self):
        return cache.get(self.get_cache_key(), default={})


    def is_full(self):
        return self.player1 and self.player2

    def delete_second(self):
        self.player2 = None
        self.save()

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

    def init_game_state(self):
        game_state = {
            "disc1": 0,
            "disc2": 0,
            "posx": 200,
            "posy": 200,
            "pos1": 100,
            "pos2": 100,
            "vecx": 1,
            "vecy": 1,
            "mov1": 0,
            "mov2": 0,
            "move_until1": 0,
            "move_until2": 0,
            "paused": 0,
            "paused1": 0,
            "paused2": 0,
            "centered": 0,
            "playing": 0,
            "score1":0,
            "score2":0,
            "won": 0,
            'online': 0,
            "start": time.time(),
            "last_update": 0,
        }
        self.set_game_state(game_state)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)