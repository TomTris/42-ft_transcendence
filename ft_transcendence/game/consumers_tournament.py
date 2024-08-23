from asgiref.sync import async_to_sync
from django.core.cache import cache
import time
import math
from .models import width, height, pwidth, pheight, radius, distance
import random
from .utils import Player, generate_random_angle, simulate_ball_position

import json
from .consumers_offline import BaseConsumer
import threading


class TournamentConsumer(BaseConsumer):

    def get_cache_key(self):
        return f'game_tournament{self.user.id}'

    def set_game_state(self, game_state):
        cache.set(self.get_cache_key(), game_state, timeout=None)

    def get_game_state(self):
        return cache.get(self.get_cache_key(), default={})

    def connect(self):
        self.accept()
        self.user = self.scope['user'] 
        data = self.get_game_state()
        if data:
            self.game_state = data
        else:
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
                "in1":"",
                "in2":"",
                "in3":"",
                "in4":"",
                "p1": "",
                "p2": "",
                "p3": "",
                "p4": "",
                "score1_1": 0,
                "score1_2": 0,
                "score2_1": 0,
                "score2_2": 0,
                "score3_1": 0,
                "score3_2": 0,
                "current_game": 0,
                "waiting": 0,
                "move_until1": 0,
                "move_until2": 0,
                "paused": 0,
                "paused1": 0,
                "paused2": 0,
                "centered": 0,
                "playing": 0,
                "score1":0,
                "score2":0,
                "left":0,
                "won": 0,
                "start": time.time() + 4,
                "last_update": 0,
            }
        self.set_game_state(self.set_game_state)
        self.game_state_lock = threading.Lock()
        self.stop_thread = threading.Event()
        self.periodic_task = threading.Thread(target=self.start, daemon=True)
        self.periodic_task.start()


    def disconnect(self, code):
        with self.game_state_lock:
            self.game_state['paused'] = 1
            self.set_game_state(self.game_state)
            self.stop_thread.set()
            if self.periodic_task.is_alive():
                self.periodic_task.join()


    def get_status(self):
        if self.game_state['in1'] == '':
            status = 'Input'
        elif self.game_state['waiting'] == 1:
            status = 'Waiting'
        elif self.game_state['won'] != 0:
            status = 'Won'
        elif self.game_state['paused'] != 0:
            status = "Paused"
        elif self.game_state['start'] - time.time() >= 0.0:
            status = "Count down"
        else:
            status = "Playing"
        return status



    def send_data(self):
        message = {
            'status': self.get_status(),
            'player1':'left',
            'player2':'right',
            'disc1':self.game_state['disc1'],
            'disc2':self.game_state['disc2'],
            'current_player': 1,
            'pos1':self.game_state['pos1'],
            'pos2':self.game_state['pos2'],
            'posx':self.game_state['posx'],
            'posy':self.game_state['posy'],
            'score1': self.game_state['score1'],
            'score2': self.game_state['score2'],
            'pheight': pheight,
            'pwidth': pwidth,
            'radius': radius,
            'width': width,
            'height': height,
            'paused':self.game_state['paused'],
            'vecy': self.game_state['vecy'],
            'vecx': self.game_state['vecx'],
            'distance': distance, 
            'time':self.get_time(),
        }
        self.send(text_data=json.dumps(message))


    def update_playing(self):
        if self.game_state['waiting'] == 1:
            if self.game_state['playing'] == 1:
                self.game_state['playing'] = 0
            return
        if self.game_state['paused'] == 0:
            if self.game_state['start'] < time.time():
                if self.game_state['playing'] == 0:
                    self.game_state['playing'] = 1
                    self.game_state['last_update'] = time.time()
        else:
            if self.game_state['playing'] == 1:
                self.game_state['playing'] = 0


    def start(self):
        while not self.stop_thread.is_set():
            with self.game_state_lock:
                self.update_playing()
                if self.game_state['centered'] == 0:
                    self.position_center_random_move()
                elif self.game_state['playing']:
                    self.make_move()
                self.send_data()
                time.sleep(0.0167)



    def receive(self, text_data):
        print(text_data)

