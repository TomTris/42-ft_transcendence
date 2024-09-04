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
        self.user.is_playing = True
        self.user.save()
        data = self.get_game_state()
        if data:
            self.game_state = data
            self.game_state['disconected'] = 0
            self.game_state['send'] = 1
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
                "player1": "",
                "player2": "",
                "player3": "",
                "player4": "",
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
                "games_played": 0,
                "centered": 0,
                "playing": 0,
                "score1":4,
                "score2":4,
                "left":0,
                "won": 0,
                "finished": 0,
                "start": time.time() + 4,
                "time_passed":0,
                "last_update": 0,
                "disconected": 0,
                "send": 1,
                "input": 1,
            }
        self.set_game_state(self.game_state)
        self.game_state_lock = threading.Lock()
        self.periodic_task = threading.Thread(target=self.start, daemon=True)
        self.periodic_task.start()


    def disconnect(self, code):
        with self.game_state_lock:
            self.user.is_playing = False
            self.user.save()
            self.game_state['paused'] = 1
            self.game_state['disconected'] = 1
            self.set_game_state(self.game_state)



    def get_status(self):
        if self.game_state['input'] == 1:
            status = 'Input'
        elif self.game_state['finished'] == 1:
            status = 'Finished'
        elif self.game_state['waiting'] == 1:
            status = 'Waiting'
        elif self.game_state['paused'] != 0:
            status = "Paused"
        elif self.game_state['start'] - time.time() >= 0.0:
            status = "Count down"
        else:
            status = "Playing"
        return status


    def get_player1(self):
        if self.game_state['games_played'] == 0:
            return self.game_state['player1']
        elif self.game_state['games_played'] == 1:
            return self.game_state['player3']
        else:
            if self.game_state['score1_1'] > self.game_state['score1_2']:
                return self.game_state['player1']
            else:
                return self.game_state['player2']

    def get_player2(self):
        if self.game_state['games_played'] == 0:
            return self.game_state['player2']
        elif self.game_state['games_played'] == 1:
            return self.game_state['player4']
        else:
            if self.game_state['score2_1'] > self.game_state['score2_2']:
                return self.game_state['player3']
            else:
                return self.game_state['player4']


    def get_winner(self):
        if self.game_state['games_played'] == 0:
            return ""
        if self.game_state['games_played'] == 1:
            if self.game_state['score1_1'] > self.game_state['score1_2']:
                return self.game_state['player1']
            else:
                return self.game_state['player2']
        if self.game_state['games_played'] == 2:
            if self.game_state['score2_1'] > self.game_state['score2_2']:
                return self.game_state['player3']
            else:
                return self.game_state['player4']
        if self.game_state['games_played'] == 3:
            if self.game_state['score3_1'] > self.game_state['score3_2']:
                self.get_player1()
            else:
                self.get_player2()

    def get_looser(self):
        if self.game_state['games_played'] == 0:
            return ""
        if self.game_state['games_played'] == 1:
            if self.game_state['score1_1'] < self.game_state['score1_2']:
                return self.game_state['player1']
            else:
                return self.game_state['player2']
        if self.game_state['games_played'] == 2:
            if self.game_state['score2_1'] < self.game_state['score2_2']:
                return self.game_state['player3']
            else:
                return self.game_state['player4']
        if self.game_state['games_played'] == 3:
            if self.game_state['score3_1'] < self.game_state['score3_2']:
                self.get_player1()
            else:
                self.get_player2()


    def send_data(self):
        message = {
            'status': self.get_status(),
            'player1': self.get_player1(),
            'player2': self.get_player2(),
            'disc1':self.game_state['disc1'],
            'disc2':self.game_state['disc2'],
            'winner': self.get_winner(),
            'loser': self.get_looser(),
            'won': self.game_state['won'],
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
            'in1':self.game_state['in1'],
            'in2':self.game_state['in2'],
            'in3':self.game_state['in3'],
            'in4':self.game_state['in4'],
        }
        self.send(text_data=json.dumps(message))
        if message['status'] in ['Finished', 'Input', 'Waiting']:
            self.game_state['send'] = 0


    def update_playing(self):
        if self.game_state['waiting'] == 1 or self.game_state['in1'] == '' or self.game_state['finished'] == 1:
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

    def set_score(self):
        if self.game_state['games_played'] == 1:
            self.game_state['score1_1'] = self.game_state['score1']
            self.game_state['score1_2'] = self.game_state['score2']
        if self.game_state['games_played'] == 2:
            self.game_state['score2_1'] = self.game_state['score1']
            self.game_state['score2_2'] = self.game_state['score2']
        if self.game_state['games_played'] == 3:
            self.game_state['score3_1'] = self.game_state['score1']
            self.game_state['score3_2'] = self.game_state['score2']

    def start(self):
        while True:
            with self.game_state_lock:
                if self.game_state['won'] != 0 and self.game_state['send'] == 1:
                    self.game_state['games_played'] += 1
                    self.set_score()
                    self.game_state['waiting'] = 1
                    if self.game_state['games_played'] >= 3:
                        self.game_state['finished'] = 1
                if self.game_state['disconected'] == 1:
                    return
                self.update_playing()
                if self.game_state['centered'] == 0:
                    self.position_center_random_move()
                elif self.game_state['playing']:
                    self.make_move()

                if self.game_state['send'] == 1:
                    self.send_data()
            time.sleep(0.005)



    def receive(self, text_data):
        data = json.loads(text_data)
        print(data['type'])
        with self.game_state_lock:
            if data['type'] == 'input':
                self.game_state['in1'] = data['player1']
                self.game_state['in2'] = data['player2']
                self.game_state['in3'] = data['player3']
                self.game_state['in4'] = data['player4']
                players = [data['player1'], data['player2'], data['player3'], data['player4']]
                random.shuffle(players)
                print(players)
                self.game_state['player1'] = players[0]
                self.game_state['player2'] = players[1]
                self.game_state['player3'] = players[2]
                self.game_state['player4'] = players[3]
                self.game_state['waiting'] = 1
                self.game_state['send'] = 1
                self.game_state['games_played'] = 0
                self.game_state['input'] = 0
                self.game_state['score1'] = 0
                self.game_state['score2'] = 0
                self.game_state['centered'] = 0
                self.game_state['finished'] = 0
                self.game_state['won'] = 0
            elif data['type'] == 'ready':
                self.game_state['send'] = 1
                self.game_state['waiting'] = 0
                self.game_state['paused'] = 0
                self.game_state['centered'] = 0
                self.game_state['won'] = 0
                self.game_state['score1'] = 4
                self.game_state['score2'] = 4
                self.game_state['start'] = time.time() + 4
            elif data['type'] == 'finished':
                self.game_state['won'] = 0
                self.game_state['input'] = 1
                self.game_state['finished'] = 0
                self.game_state['send'] = 1
            else:
                if data['key'] in ['f', 'F']:
                    self.pause()
                if data['key'] in ['w', 'W']:
                    self.move_up(1)
                if data['key'] in ['ArrowUp']:
                    self.move_up(2)
                if data['key'] in ['S', 's']:
                    self.move_down(1)
                if data['key'] in ['ArrowDown']:
                    self.move_down(2)
