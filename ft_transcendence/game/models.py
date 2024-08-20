from django.db import models
from django.conf import settings
import time
import random
import math

width = 800
height = 400
pheight = 80
pwidth = 15
distance = 40
radius = 10
speed = 900

class GameSession(models.Model):
    player1 = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='game_player1', null=True, on_delete=models.SET_NULL)
    player2 = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='game_player2', null=True, on_delete=models.SET_NULL)
    score1 = models.IntegerField(default=0)
    score2 = models.IntegerField(default=0)
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

    
    def get_time_to_collision(self):
        vecy = self.game_state['vecy']
        vecx = self.game_state['vecx']
        posx = self.game_state['posx']
        posy = self.game_state['posy']
        if vecy > 0:
            distance = height - posy - radius 
            col_y = distance / vecy
        elif vecy < 0:
            vecy = -vecy
            distance = posy - radius
            col_y = distance / vecy
        else:
            col_y = 1e9
        
        if vecx > 0:
            distance = width - posx - radius
            col_x = distance / vecx
        elif vecx < 0:
            vecx = -vecx
            distance = posx - radius
            col_x = distance / vecx
        else:
            col_x = 1e9
        if col_x > col_y:
            return col_y, 2
        return col_x, 1


    def update_playing(self):
        if self.game_state['paused1'] or self.game_state['paused2'] or self.player2 is None or self.game_state['start'] > time.time():
            self.game_state['playing'] = 0
        else:
            self.game_state['playing'] = 1
            self.game_state['last_update'] = time.time()
        self.save()


    def make_move(self):
        delta_time = time.time() - self.game_state['last_update']
        while (1):
            if delta_time <= 0:
                break
            col_time, type = self.get_time_to_collision()
            if delta_time < col_time:
                self.game_state['posx'] += delta_time * self.game_state['vecx']
                self.game_state['posy'] += delta_time * self.game_state['vecy']
                delta_time = 0
            else:
                if type == 1:
                    self.game_state['posx'] += col_time * self.game_state['vecx']
                    self.game_state['posy'] += col_time * self.game_state['vecy']
                    self.game_state['vecx'] = -self.game_state['vecx']
                else:
                    self.game_state['posx'] += col_time * self.game_state['vecx']
                    self.game_state['posy'] += col_time * self.game_state['vecy']
                    self.game_state['vecy'] = -self.game_state['vecy']
                delta_time -= col_time

        self.game_state['last_update'] = time.time()
        self.save()
        


    def position_center_random_move(self):
        
        
        angle = random.uniform(0, 1) * 2.0 * math.pi
        self.game_state['vecx'] = math.sin(angle) * speed
        self.game_state['vecy'] = math.cos(angle) * speed
        self.game_state['posx'] = width / 2
        self.game_state['posy'] = height / 2
        self.game_state['pos1'] = height / 2 - pheight / 2
        self.game_state['pos2'] = height / 2 - pheight / 2
        self.game_state['last_update'] = time.time()
        self.game_state['mov1'] = 0
        self.game_state['mov2'] = 0
        self.game_state['centered'] = 1
        self.save()


    def init_game_state(self):
        self.game_state = {
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
            "paused1": 0,
            "paused2": 0,
            "centered": 0,
            "playing": 0,
            "start": time.time(),
            "last_update": 0,
        }
        self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)