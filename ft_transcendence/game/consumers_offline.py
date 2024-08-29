from asgiref.sync import async_to_sync
import time
import math
from .models import width, height, pwidth, pheight, radius, distance
import random
from .utils import Player, generate_random_angle, simulate_ball_position, get_factor

import json
from channels.generic.websocket import WebsocketConsumer
import threading

class BaseConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.user = self.scope['user'] 
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
            "time_passed":0,
        }
        self.game_state_lock = threading.Lock()
        self.periodic_task = threading.Thread(target=self.start, daemon=True)
        self.periodic_task.start()


    def disconnect(self, code):
        with self.game_state_lock:
            self.game_state['left'] = 1
        if self.periodic_task.is_alive():
            self.periodic_task.join()
        self.close()


    def update_playing(self):
        if self.game_state['paused'] == 0:
            if self.game_state['start'] < time.time():
                if self.game_state['playing'] == 0:
                    self.game_state['playing'] = 1
                    self.game_state['last_update'] = time.time()
        else:
            if self.game_state['playing'] == 1:
                self.game_state['playing'] = 0


    def position_center_random_move(self):
        angle = generate_random_angle()
        speed = 300

        self.game_state['vecx'] = int(math.cos(angle) * speed)
        self.game_state['vecy'] = int(math.sin(angle) * speed)
        self.game_state['posx'] = width / 2
        self.game_state['posy'] = height / 2
        self.game_state['pos1'] = height / 2 - pheight / 2
        self.game_state['pos2'] = height / 2 - pheight / 2
        self.game_state['last_update'] = time.time()
        self.game_state['mov1'] = 0
        self.game_state['mov2'] = 0
        self.game_state['centered'] = 1

    def make_move(self):
        update_time = time.time()
        delta_time = update_time - self.game_state['last_update']
        # print(delta_time)
        mov1, mov2 = 0, 0
        dts = []
        
        if self.game_state['move_until1'] > time.time():
            dts.append(delta_time)
        else:
            if self.game_state['last_update'] < self.game_state['move_until1']:
                dts.append(self.game_state['move_until1'] - self.game_state['last_update'])
            else:
                dts.append(0)

        if self.game_state['move_until2'] > time.time():
            dts.append(delta_time)
        else:
            if self.game_state['last_update'] < self.game_state['move_until2']:
                dts.append(self.game_state['move_until2'] - self.game_state['last_update'])
            else:
                dts.append(0)

        mov1 = self.game_state['mov1']
        mov2 = self.game_state['mov2']
        players = []
        s = 200 * get_factor(self.game_state['time_passed'])
        players.append(Player(distance, self.game_state['pos1'], pwidth, pheight, width, height, mov1, speed=s))
        players.append(Player(width - distance - pwidth, self.game_state['pos2'], pwidth, pheight, width, height, mov2, speed=s))
        pos_x, pos_y, vecx, vecy, p = simulate_ball_position(self.game_state['posx'], self.game_state['posy'], self.game_state['vecx'], self.game_state['vecy'], delta_time, players, dts, self.game_state['time_passed'])
        
        vecx, vecy = self.update_speed(vecx, vecy, self.game_state['time_passed'], delta_time)
        self.game_state['time_passed'] += delta_time
        self.game_state['posx'] = pos_x
        self.game_state['posy'] = pos_y
        self.game_state['vecx'] = vecx
        self.game_state['vecy'] = vecy
        self.game_state['pos1'] = players[0].y
        self.game_state['pos2'] = players[1].y
        if p != 0:
            if p == 1:
                self.game_state["score1"] += 1
                if self.game_state["score1"] == 5:
                    self.game_state["start"] = time.time() + 1000000
                    self.game_state["won"] = 1
                else:
                    self.game_state["centered"] = 0
                    self.game_state["start"] = time.time() + 3
                    self.game_state['time_passed'] = 0
            else:
                self.game_state["score2"] += 1
                if self.game_state["score2"] == 5:
                    self.game_state["won"] = 2
                    self.game_state["start"] = time.time() + 1000000
                else:
                    self.game_state["centered"] = 0
                    self.game_state['time_passed'] = 0
                    self.game_state["start"] = time.time() + 3
            self.game_state["playing"] = 0
        self.game_state['last_update'] = update_time


    def start(self):
        while (1):
            with self.game_state_lock:
                if self.game_state['left'] != 0:
                    break
                self.update_playing()
                if self.game_state['centered'] == 0:
                    self.position_center_random_move()
                elif self.game_state['playing']:
                    self.make_move()
                self.send_data()
            time.sleep(0.0167)

    def get_time(self):
        return int(self.game_state['start'] - time.time())

    def get_status(self):
        if self.game_state['won'] != 0:
            status = 'Won'
        elif self.game_state['paused'] != 0:
            status = "Paused"
        elif self.game_state['start'] - time.time() >= 0.0:
            status = "Count down"
        else:
            status = "Playing"
        return status


    def move_up(self, player):
        if player == 1:
            self.game_state['move_until1'] = time.time() + 0.25
            self.game_state['mov1'] = -1
        else:
            self.game_state['move_until2'] = time.time() + 0.25
            self.game_state['mov2'] = -1


    def move_down(self, player):
        if player == 1:
            self.game_state['move_until1'] = time.time() + 0.25
            self.game_state['mov1'] = 1
        else:
            self.game_state['move_until2'] = time.time() + 0.25
            self.game_state['mov2'] = 1


    def pause(self):
        if self.game_state['paused'] == 0:
            self.game_state['paused'] = 1
        else:
            self.game_state['paused'] = 0
            self.game_state['start'] = time.time() + 4


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



class OfflineConsumer(BaseConsumer):

    def receive(self, text_data):
        data = json.loads(text_data)
        with self.game_state_lock:
            if data['key'] in ['f', "F"]:
                self.pause()
            elif data['key'] in ['W', 'w']:
                self.move_up(1)
            elif data['key'] in ['ArrowUp']:
                self.move_up(2)
            elif data['key'] in ['S', 's']:
                self.move_down(1)
            elif data['key'] in ['ArrowDown']:
                self.move_down(2)


class AIConsumer(BaseConsumer):


    def best_ai(self):
        i = random.randint(0, 2)
        if i == 0:
            self.move_up(2)
        elif i == 1:
            self.move_down(2)

    def start(self):
        counter = 0
        while (1):
            with self.game_state_lock:
                if self.game_state['left'] != 0:
                    break
                if counter == 0:
                    self.best_ai()
                self.update_playing()
                if self.game_state['centered'] == 0:
                    self.position_center_random_move()
                elif self.game_state['playing']:
                    self.make_move()
                self.send_data()
                time.sleep(0.0167)
            counter += 1
            counter %= 6

    def send_data(self):
        message = {
            'status': self.get_status(),
            'player1': self.user.login,
            'player2':'bot',
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


    def receive(self, text_data):
        data = json.loads(text_data)
        with self.game_state_lock:
            if data['key'] in ['f', "F"]:
                self.pause()
            elif data['key'] in ['W', 'w', 'ArrowUp']:
                self.move_up(1)
            elif data['key'] in ['S', 's', 'ArrowDown']:
                self.move_down(1)