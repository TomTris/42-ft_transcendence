from django.db import models
from django.conf import settings
import time
import random
import math
from django.core.cache import cache

width = 1000
height = 600
pheight = 120
pwidth = 15
distance = 40
radius = 10
speed = 300

class GameSession(models.Model):
    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='game_player1', null=True, on_delete=models.SET_NULL)
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='game_player2', null=True, on_delete=models.SET_NULL)
    score1 = models.IntegerField(default=0)
    score2 = models.IntegerField(default=0)
    rank_change1 = models.IntegerField(default=0)
    rank_change2 = models.IntegerField(default=0)
    connected = models.BooleanField(default=False)
    is_tournament = models.BooleanField(default=False)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='winner', null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tournament_id = models.IntegerField(default=0)

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
            "score1":4,
            "score2":4,
            "won": 0,
            'online': 0,
            "start": time.time(),
            "last_update": 0,
            "connected1":0,
            "connected2":0,
            "time_passed":0,
            'started':0,
            'm1':-1,
            'm2':-1,
            'must_update':0,
            'prev':'',
            'start2':0
        }
        self.set_game_state(game_state)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class TournamentSession(models.Model):
    name = models.CharField(max_length=40, null=True)

    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tournament1', null=True, on_delete=models.SET_NULL)
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tournament2', null=True, on_delete=models.SET_NULL)
    player3 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tournament3', null=True, on_delete=models.SET_NULL)
    player4 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tournament4', null=True, on_delete=models.SET_NULL)
    
    is_active = models.BooleanField(default=True)
    code = models.CharField(max_length=10, unique=True)

    game1 = models.ForeignKey(GameSession, related_name='game1', null=True, on_delete=models.SET_NULL)
    game2 = models.ForeignKey(GameSession, related_name='game2', null=True, on_delete=models.SET_NULL)
    game3 = models.ForeignKey(GameSession, related_name='game3', null=True, on_delete=models.SET_NULL)

    def get_cache_key(self):
        return f'online_tournament_{self.id}'

    def set_tournament_state(self, game_state):
        cache.set(self.get_cache_key(), game_state, timeout=None)  # Timeout can be set according to your needs

    def get_tournament_state(self):
        return cache.get(self.get_cache_key(), default={})
    
    def is_full(self):
        return self.player1 and self.player2 and self.player3 and self.player4
    
    def delete_player(self, user):
        if self.player2 == user:
            self.player2 = None
        if self.player3 == user:
            self.player3 = None
        if self.player4 == user:
            self.player4 = None
        
    def is_player_in(self, player):
        if player in [self.player1, self.player2, self.player3, self.player4]:
            return True
        return False


    def add_player(self, user):
        if not self.player1:
            self.player1 = user
        elif not self.player2:
            self.player2 = user
        elif not self.player3:
            self.player3 = user
        elif not self.player4:
            self.player4 = user
        else:
            raise ValueError("Game session is already full")
        self.save()

    def init_tournament_state(self):
        game_state = {
            'status':'Waiting',
            'score1_1':0,
            'score1_2':0,
            'score2_1':0,
            'score2_2':0,
            'score3_1':0,
            'score3_2':0,
            'joined1_1':0,
            'joined1_2':0,
            'joined2_1':0,
            'joined2_2':0,
            'joined3_1':0,
            'joined3_2':0,
            'tournament_started':0,
            'confirmed':0,
            'finished1':0,
            'finished2':0,
            'finished3':0,
            'start1':0,
            'start2':0,
            'game1_id':0,
            'game2_id':0,
            'game3_id':0,
            'final1':0,
            'final2':0,
            'pos1':0,
            'pos2':0,
            'pos3_1':0,
            'pos3_2':0,
            'm1':-1,
            'm2':-1,
            'm3':-1,
            'm4':-1,
            'start':0
        }
        self.set_tournament_state(game_state)
        