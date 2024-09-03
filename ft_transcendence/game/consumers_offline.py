from asgiref.sync import async_to_sync
import time
import math
from .models import width, height, pwidth, pheight, radius, distance
import random
from .utils import Player, generate_random_angle, simulate_ball_position, get_factor, update_speed

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
        
        vecx, vecy = update_speed(vecx, vecy, self.game_state['time_passed'], delta_time)
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
            time.sleep(0.005)

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


    def move_up(self, player, default_time=0.25):
        if player == 1:
            self.game_state['move_until1'] = time.time() + default_time
            self.game_state['mov1'] = -1
        else:
            self.game_state['move_until2'] = time.time() + default_time
            self.game_state['mov2'] = -1


    def move_down(self, player, default_time=0.25):
        if player == 1:
            self.game_state['move_until1'] = time.time() + default_time
            self.game_state['mov1'] = 1
        else:
            self.game_state['move_until2'] = time.time() + default_time
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

    def get_distance(self):
        if self.game_state['vecx'] > 0:
            return width - self.game_state['posx'] - distance - pwidth
        else:
            return self.game_state['posx'] - distance - pwidth + width - 2 * (pwidth + distance)

    def get_y_cord(self, y_distance):
        
        if self.game_state['vecy'] > 0:
            y_distance += self.game_state['posy']   
        else:
            y_distance += height - self.game_state['posy'] + height
        
        if int(y_distance // height) % 2 == 1:
            return height - y_distance % height
        else:
            return y_distance % height

    def get_best_move(self, y_cord):
        top_pos = self.game_state['pos2'] + 20
        bottom_pos = self.game_state['pos2'] + pheight - 20
        speed = get_factor(self.game_state['time_passed']) * 200
        t = abs(self.game_state['pos2'] + pheight / 2 - y_cord) / speed
        if y_cord < top_pos:
            return 1, t
        if y_cord > bottom_pos:
            return 2, t
        return 0, 0


    def best_ai(self):
        x_distance = self.get_distance()
        if x_distance < 0:
            return
        y_distance = abs(x_distance / self.game_state['vecx'] * self.game_state['vecy'])
        y_cord = self.get_y_cord(y_distance)
        best_move, timing = self.get_best_move(y_cord)
        if best_move == 2:
            self.move_down(2, timing)
        if best_move == 1:
            self.move_up(2, timing)


    def start(self):
        last = 0
        while (1):
            with self.game_state_lock:
                if self.game_state['left'] != 0:
                    break
                if time.time() >= last + 1:
                    self.best_ai()
                    last = time.time()
                self.update_playing()
                if self.game_state['centered'] == 0:
                    self.position_center_random_move()
                elif self.game_state['playing']:
                    self.make_move()
                self.send_data()
            time.sleep(0.005)

    def send_data(self):
        message = {
            'status': self.get_status(),
            'player1': self.user.username,
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