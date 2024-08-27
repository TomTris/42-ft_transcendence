import json
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import GameSession
from channels.layers import get_channel_layer
import threading
from asgiref.sync import async_to_sync
import time
import math
import random
from .models import width, height, pwidth, pheight, radius, distance
from .utils import Player, generate_random_angle, simulate_ball_position

counter = 1

class GameConsumer(WebsocketConsumer):
    def connect(self):
        
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'game_{self.session_id}'
        self.game_session = GameSession.objects.filter(id=self.session_id).first()
        if self.game_session is None:
            self.close()
            return
        if not self.game_session.is_active:
            self.close()
            return
        
        self.user = self.scope['user']
        if self.user in [self.game_session.player1, self.game_session.player2]:
            
            self.accept()
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
            t = 0
            game_state = self.game_session.get_game_state()
            self.update_game_session()
            if self.user == self.game_session.player1:
                game_state['disc1'] = 0
                if self.game_session.player1 == self.game_session.player2:
                    self.game_session.delete_second()
                    t = 1
            else:
                game_state['disc2'] = 0
            if game_state['disc1'] == 0 and game_state['disc2'] == 0 and game_state['paused'] == 0:
                if self.game_session.is_tournament:
                    if self.user == self.game_session.player1 and game_state['connected2'] == 0:
                        game_state['start'] = (time.time() + 31)
                        game_state['connected1'] = 1
                    elif self.user == self.game_session.player2 and game_state['connected1'] == 0:
                        game_state['start'] = (time.time() + 31)
                        game_state['connected1'] = 1
                else:
                    game_state['start'] = time.time() + 4
                game_state['playing'] = 0
            self.game_session.set_game_state(game_state)
        else:
            self.close()
            return  
       
        self.game_state_lock = threading.Lock()
        if self.user == self.game_session.player1 and t == 0:
            self.periodic_task = threading.Thread(target=self.send_data, daemon=True)
            self.periodic_task.start()
        self.update_game_session()

    def update_game_session(self):
        message = {
            "value":"fun"
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'session_update',  # Must match the method name in this consumer
                'message': message
            }
        )

    def session_update(self, event):
        self.game_session = GameSession.objects.filter(id=self.session_id).first()


    def ensure(self):
        time.sleep(0.2)
        self.game_session = GameSession.objects.filter(id=self.session_id).first()
        with self.game_state_lock:
            game_state = self.game_session.get_game_state()
            if game_state['online'] == self.count and game_state['disc1'] == 1:
                self.game_session.delete()
            else:
                if self.game_session.player1 == self.game_session.player2:
                    self.game_session.delete_second()
                game_state['online'] = 0
        self.game_session.set_game_state(game_state)
        self.update_game_session()

    def disconecting(self):
        if not self.game_session.is_tournament:
            try:
                self.game_session.add_player(self.user)
                self.game_session.save()
            except Exception:
                return
            self.periodic_task = threading.Thread(target=self.ensure, daemon=True)
            self.periodic_task.start()


    def disconnect(self, close_code):
        self.game_session = GameSession.objects.filter(id=self.session_id).first()
        if self.game_session is None:
            return
        with self.game_state_lock:
            if self.game_session.is_active:
                game_state = self.game_session.get_game_state()
                if self.user == self.game_session.player1:
                    if self.game_session.player2 is None:
                        global counter
                        self.count = counter
                        counter += 1
                        game_state['online'] = self.count
                        self.disconecting()
                    game_state['disc1'] = 1
                    if game_state['paused1'] != 2:
                        game_state['paused'] = 1
                        game_state['paused1'] += 1
                        game_state['start'] = time.time() + 21
                else:
                    game_state['disc2'] = 1
                    if game_state['paused2'] != 2:
                        game_state['paused'] = 2
                        game_state['paused2'] += 1
                        game_state['start'] = time.time() + 21

                self.game_session.set_game_state(game_state)
                if game_state['disc1'] == 1 and game_state['disc2'] == 1 and self.game_session.is_active and not self.game_session.is_tournament:
                    self.game_session.delete()
                    return
            
            self.send_data_to_group()


    def calculate_rank_change(self, elo1, elo2, win, factor=16):
        e1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
        if win == 1:
            e = 1 - e1 
        else:
            e = 0 - e1
        e = abs(e)
        result = e * factor
        return math.ceil(result)


    def save_to_data_base(self):
        self.game_session = GameSession.objects.filter(id=self.session_id).first()
        if self.game_session.is_active:
            self.game_session.is_active = False
            game_state = self.game_session.get_game_state()
            self.game_session.score1 = game_state['score1']
            self.game_session.score2 = game_state['score2']
            if game_state['won'] == 1:
                self.game_session.winner = self.game_session.player1
            else:
                self.game_session.winner = self.game_session.player2
            
            if self.game_session.is_tournament == False:
                rank_change = self.calculate_rank_change(self.game_session.player1.elo, self.game_session.player2.elo, game_state['won'])
                elo1 = self.game_session.player1.elo
                elo2 = self.game_session.player2.elo
                if game_state['won'] == 1:
                    elo1 += rank_change
                    elo2 -= rank_change
                else:
                    elo2 += rank_change
                    elo1 -= rank_change
                if elo2 < 0:
                    elo2 = 0
                if elo1 < 0:
                    elo1 = 0
                self.game_session.rank_change1 = elo1 - self.game_session.player1.elo
                self.game_session.rank_change2 = elo2 - self.game_session.player2.elo
                self.game_session.player1.elo = elo1
                self.game_session.player2.elo = elo2
            self.game_session.player1.total += 1
            self.game_session.player2.total += 1
            if game_state['won'] == 1:
                self.game_session.player1.wins += 1
                self.game_session.player2.loses += 1
            else:
                self.game_session.player2.wins += 1
                self.game_session.player1.loses += 1
            self.game_session.player1.save()
            self.game_session.player2.save()
            self.game_session.save()


    def update_playing(self):
        game_state = self.game_session.get_game_state()
        if self.game_session.is_tournament:
            if game_state['disc1'] == 1 and game_state['disc2'] == 1:
                if game_state['start'] < time.time():
                    game_state['playing'] = 1
                    self.game_session.set_game_state(game_state)
                return
        if game_state['paused'] == 0 and self.game_session.player2 is not None:
            if game_state['start'] < time.time():
                if game_state['playing'] == 0:
                    game_state['playing'] = 1
                    game_state['last_update'] = time.time()
                    self.game_session.set_game_state(game_state)
        else:
            if game_state['playing'] == 1:
                game_state['playing'] = 0
                self.game_session.set_game_state(game_state)



    def position_center_random_move(self):
        game_state = self.game_session.get_game_state()
        angle = generate_random_angle()
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
        self.game_session.set_game_state(game_state)



    def send_data(self):
        while(self.game_session and self.game_session.is_active):
            with self.game_state_lock:
                game_state = self.game_session.get_game_state()
                if not game_state:
                    return
                self.update_playing()
                if game_state['centered'] == 0:
                    self.position_center_random_move()
                elif game_state['playing']:
                    self.make_move()
                self.send_data_to_group()
            time.sleep(0.0167)
    
    def pause(self, ind):
       
        game_state = self.game_session.get_game_state()
        if ind:
            if game_state['paused'] == 0:
                if game_state['paused1'] != 2:
                    game_state['paused'] = 1
                    game_state['paused1'] += 1
                    game_state['start'] = time.time() + 21
            else:
                if game_state['paused'] == 1:
                    game_state['paused'] = 0
                    game_state['start'] = time.time() + 4
                else:
                    if game_state['start'] < time.time():
                        game_state['paused'] = 0
                        game_state['start'] = time.time() + 4
        else:
            if game_state['paused'] == 0:
                if game_state['paused2'] != 2:
                    game_state['paused'] = 2
                    game_state['paused2'] += 1
                    game_state['start'] = time.time() + 21
            else:
                if game_state['paused'] == 2:
                    game_state['paused'] = 0
                    game_state['start'] = time.time() + 4
                else:
                    if game_state['start'] < time.time():
                        game_state['paused'] = 0
                        game_state['start'] = time.time() + 4
        self.game_session.set_game_state(game_state)


    def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'keydown':
            with self.game_state_lock:
                if data['key'] in ['ArrowUp', 'w', 'W']:
                    self.move_up(self.user == self.game_session.player1)
                elif data['key'] in ['ArrowDown', 's', 'S']:
                    self.move_down(self.user == self.game_session.player1)
                elif data['key'] in ['f', 'F']:
                    self.pause(self.user == self.game_session.player1)
        else:
            response = {}
            response['status'] = 'cancel'
            if self.game_session.player2 is None:
                response['message'] = 'ok'
                self.game_session.delete()
            else:
                response['message'] = 'not ok'
            self.send(text_data=json.dumps(response))

    def make_move(self):
        game_state = self.game_session.get_game_state()
        update_time = time.time()
        delta_time = update_time - game_state['last_update']
        mov1, mov2 = 0, 0
        dts = []
        
        if game_state['move_until1'] > time.time():
            dts.append(delta_time)
        else:
            if game_state['last_update'] < game_state['move_until1']:
                dts.append(game_state['move_until1'] - game_state['last_update'])
            else:
                dts.append(0)

        if game_state['move_until2'] > time.time():
            dts.append(delta_time)
        else:
            if game_state['last_update'] < game_state['move_until2']:
                dts.append(game_state['move_until2'] - game_state['last_update'])
            else:
                dts.append(0)

        mov1 = game_state['mov1']
        mov2 = game_state['mov2']
        players = []
        players.append(Player(distance, game_state['pos1'], pwidth, pheight, width, height, mov1, speed=200))
        players.append(Player(width - distance - pwidth, game_state['pos2'], pwidth, pheight, width, height, mov2, speed=200))
        pos_x, pos_y, vecx, vecy, p = simulate_ball_position(game_state['posx'], game_state['posy'], game_state['vecx'], game_state['vecy'], delta_time, players, dts)
        game_state['posx'] = pos_x
        game_state['posy'] = pos_y
        game_state['vecx'] = vecx
        game_state['vecy'] = vecy
        game_state['pos1'] = players[0].y
        game_state['pos2'] = players[1].y
        if p != 0:
            if p == 1:
                game_state["score1"] += 1
                if game_state["score1"] == 5:
                    game_state["start"] = time.time() + 1000000
                    game_state["won"] = 1
                    self.game_session.set_game_state(game_state)
                    self.save_to_data_base()
                    self.update_game_session()
                    self.send_data_to_group()
                else:
                    game_state["centered"] = 0
                    game_state["start"] = time.time() + 3
            else:
                game_state["score2"] += 1
                if game_state["score2"] == 5:
                    game_state["won"] = 2
                    game_state["start"] = time.time() + 1000000
                    self.game_session.set_game_state(game_state)
                    self.save_to_data_base()
                    self.update_game_session()
                    self.send_data_to_group()
                else:
                    game_state["centered"] = 0
                    game_state["start"] = time.time() + 3
            game_state["playing"] = 0
            

        game_state['last_update'] = update_time
        self.game_session.set_game_state(game_state)

    def move_up(self, player):
        game_state = self.game_session.get_game_state()
        if player == 1:
            game_state['mov1'] = -1
            game_state['move_until1'] = time.time() + 0.25
        else:
            game_state['mov2'] = -1
            game_state['move_until2'] = time.time() + 0.25
        self.game_session.set_game_state(game_state)


    def move_down(self, player):
        game_state = self.game_session.get_game_state()
        if player == 1:
            game_state['mov1'] = 1
            game_state['move_until1'] = time.time() + 0.25
        else:
            game_state['mov2'] = 1
            game_state['move_until2'] = time.time() + 0.25
        self.game_session.set_game_state(game_state)


    def get_player(self, ind):
        if ind == 1:
            player = self.game_session.player1.login if self.game_session.player1 else 'Waiting...'
        else:
            player = self.game_session.player2.login if self.game_session.player2 else 'Waiting...'
        return player
    

    def get_status(self):
        game_state = self.game_session.get_game_state()
        if game_state['won'] != 0:
            status = 'Won'
        elif self.game_session.player2 is None or self.game_session.player1 is None or game_state['online'] != 0:
            status = "Waiting for other player"
        elif game_state['paused'] != 0:
            status = "Paused"
        elif game_state['start'] - time.time() >= 0.0:
            status = "Count down"
        else:
            status = "Playing"
        return status
    
    
    def get_time(self):
        game_state = self.game_session.get_game_state()
        return int(game_state['start'] - time.time())

    
    def send_data_to_group(self):
        game_state = self.game_session.get_game_state()
        message = {
                'status':self.get_status(),
                'player1':self.get_player(1),
                'player2':self.get_player(2),
                'disc1':game_state['disc1'],
                'disc2':game_state['disc2'],
                'current_player': int(self.game_session.player1 != self.user) + 1,
                'rank_change1': self.game_session.rank_change1,
                'rank_change2': self.game_session.rank_change2,
                'pos1':game_state['pos1'],
                'pos2':game_state['pos2'],
                'posx':game_state['posx'],
                'posy':game_state['posy'],
                'score1': game_state['score1'],
                'score2': game_state['score2'],
                'pheight': pheight,
                'pwidth': pwidth,
                'radius': radius,
                'width': width,
                'height': height,
                'paused':game_state['paused'],
                'vecy': game_state['vecy'],
                'vecx': game_state['vecx'],
                'distance': distance, 
                'time':self.get_time(),
                'is_tournament': int(self.game_session.is_tournament),
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'game_update',  # Must match the method name in this consumer
                'message': message
            }
        )
        # print(message)
    
    
    def game_update(self, event):
        message = event['message']
        self.send(text_data=json.dumps(message))