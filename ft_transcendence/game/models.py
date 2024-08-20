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
    player1 = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='game_player1', null=True, on_delete=models.SET_NULL)
    player2 = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='game_player2', null=True, on_delete=models.SET_NULL)
    score1 = models.IntegerField(default=0)
    score2 = models.IntegerField(default=0)
    rank_change1 = models.IntegerField(default=0)
    rank_change2 = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_cache_key(self):
        return f'game_state_{self.id}'

    def set_game_state(self, game_state):
        cache.set(self.get_cache_key(), game_state, timeout=None)  # Timeout can be set according to your needs

    def get_game_state(self):
        return cache.get(self.get_cache_key(), default={})


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

    


    def update_playing(self):
        game_state = self.get_game_state()
        if game_state['paused1'] or game_state['paused2'] or self.player2 is None or game_state['start'] > time.time():
            if game_state['playing'] == 1:
                game_state['playing'] = 1
                self.set_game_state(game_state)
        else:
            if game_state['playing'] == 0:
                game_state['playing'] = 1
                game_state['last_update'] = time.time()
                self.set_game_state(game_state)


    def simulate_ball_position(self, x, y, dx, dy, dt):
        new_x = x + dx * dt
        new_y = y + dy * dt

        # Check for collisions with the walls and adjust the position and velocity
        if new_x - radius <= 0:  # Left wall collision
            new_x = 2 * radius - new_x
            dx = -dx
        elif new_x + radius >= width:  # Right wall collision
            new_x = 2 * (width - radius) - new_x
            dx = -dx

        if new_y - radius <= 0:  # Bottom wall collision
            new_y = 2 * radius - new_y
            dy = -dy
        elif new_y + radius >= height:  # Top wall collision
            new_y = 2 * (height - radius) - new_y
            dy = -dy

        return new_x, new_y, dx, dy


    def make_move(self):
        game_state = self.get_game_state()
        update_time = time.time()
        delta_time = update_time - game_state['last_update']
        # print(delta_time)
        pos_x, pos_y, vecx, vecy = self.simulate_ball_position(game_state['posx'], game_state['posy'], game_state['vecx'], game_state['vecy'], delta_time)
        game_state['posx'] = pos_x
        game_state['posy'] = pos_y
        game_state['vecx'] = vecx
        game_state['vecy'] = vecy
        game_state['last_update'] = update_time
        self.set_game_state(game_state)

    def position_center_random_move(self):
        game_state = self.get_game_state()
        angle = random.uniform(0, 1) * 2.0 * math.pi
        speed = 300
        game_state['vecx'] = int(math.sin(angle) * speed)
        game_state['vecy'] = int(math.cos(angle) * speed)
        game_state['posx'] = width / 2
        game_state['posy'] = height / 2
        game_state['pos1'] = height / 2 - pheight / 2
        game_state['pos2'] = height / 2 - pheight / 2
        game_state['last_update'] = time.time()
        game_state['mov1'] = 0
        game_state['mov2'] = 0
        game_state['centered'] = 1
        self.set_game_state(game_state)


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
            "paused1": 0,
            "paused2": 0,
            "centered": 0,
            "playing": 0,
            "start": time.time(),
            "last_update": 0,
        }
        self.set_game_state(game_state)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)