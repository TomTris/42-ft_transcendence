import json
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import GameSession
from channels.layers import get_channel_layer
import threading
from asgiref.sync import async_to_sync
import time
import math
from .models import width, height, pwidth, pheight, radius, distance
from .utils import Player

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
        game_state = self.game_session.get_game_state()
        self.user = self.scope['user']
        if self.user in [self.game_session.player1, self.game_session.player2]:
            self.accept()
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
            
            if self.user == self.game_session.player1:
                game_state['disc1'] = 0
            else:
                game_state['disc2'] = 0
            if game_state['disc1'] == 0 and game_state['disc2'] == 0 and game_state['paused'] == 0:
                game_state['start'] = (time.time() + 4)
                game_state['playing'] = 0
            self.game_session.set_game_state(game_state)
        else:
            self.close()
            return  
        self.update_game_session()
        if self.user == self.game_session.player1:
            self.periodic_task = threading.Thread(target=self.send_data, daemon=True)
            self.periodic_task.start()


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


    def disconnect(self, close_code):
        self.game_session = GameSession.objects.filter(id=self.session_id).first()
        if self.game_session is None:
            return
        if self.game_session.is_active:
            game_state = self.game_session.get_game_state()
            if self.user == self.game_session.player1:
                if self.game_session.player2 is None:
                    self.game_session.delete()
                    return
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
            if game_state['disc1'] == 1 and game_state['disc2'] == 1 and self.game_session.is_active:
                self.game_session.delete()
                return
            
            self.send_data_to_group()
        self.close()


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
            rank_change = self.calculate_rank_change(self.game_session.player1.elo, self.game_session.player2.elo, game_state['won'])

            elo1 = self.game_session.player1.elo
            elo2 = self.game_session.player2.elo
            self.game_session.player1.total += 1
            self.game_session.player2.total += 1
            if game_state['won'] == 1:
                elo1 += rank_change
                elo2 -= rank_change
                self.game_session.player1.wins += 1
                self.game_session.player2.loses += 1
            else:
                elo2 += rank_change
                elo1 -= rank_change
                self.game_session.player2.wins += 1
                self.game_session.player1.loses += 1
            if elo2 < 0:
                elo2 = 0
            if elo1 < 0:
                elo1 = 0
            self.game_session.rank_change1 = elo1 - self.game_session.player1.elo
            self.game_session.rank_change2 = elo2 - self.game_session.player2.elo
            self.game_session.player1.elo = elo1
            self.game_session.player2.elo = elo2
            self.game_session.player1.save()
            self.game_session.player2.save()
            self.game_session.save()



    def send_data(self):
        while(self.game_session.is_active):
            game_state = self.game_session.get_game_state()
            self.game_session.update_playing()
            if game_state['centered'] == 0:
                self.game_session.position_center_random_move()
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
        if data['key'] in ['ArrowUp', 'w', 'W']:
            self.move_up(self.user == self.game_session.player1)
        elif data['key'] in ['ArrowDown', 's', 'S']:
            self.move_down(self.user == self.game_session.player1)
        elif data['key'] in ['f', 'F']:
            self.pause(self.user == self.game_session.player1)

    def simulate_ball_position(self, x, y, dx, dy, dt, players, dts):
        new_x = x + dx * dt
        new_y = y + dy * dt
        p = 0
        
        if new_x - radius <= 0:  # Left wall collision
            new_x = 2 * radius - new_x
            dx = -dx
            p = 2
        elif new_x + radius >= width:  # Right wall collision
            new_x = 2 * (width - radius) - new_x
            dx = -dx
            p = 1

        if new_y - radius <= 0:  # Bottom wall collision
            new_y = 2 * radius - new_y
            dy = -dy
        elif new_y + radius >= height:  # Top wall collision
            new_y = 2 * (height - radius) - new_y
            dy = -dy
        
        for ind, player in enumerate(players):

            player.update_pos(dts[ind])

            if (new_x + radius > player.x and new_x - radius < player.x + player.width and
            new_y + radius > player.y and new_y - radius < player.y + player.height):
            

                overlap_x = min(new_x + radius - player.x, player.x + player.width - new_x + radius)
                overlap_y = min(new_y + radius - player.y, player.y + player.height - new_y + radius)

                if overlap_x < overlap_y:

                    dx = -dx 
                    if new_x < player.x:
                        new_x = player.x - radius  # Adjust position to the left
                    else:
                        new_x = player.x + player.width + radius  # Adjust position to the right
                else:
                    dy = -dy 
                    if new_y < player.y:
                        new_y = player.y - radius  # Adjust position to the top
                    else:
                        new_y = player.y + player.height + radius  # Adjust position to the bottom

        return new_x, new_y, dx, dy, p


    def make_move(self):
        game_state = self.game_session.get_game_state()
        update_time = time.time()
        delta_time = update_time - game_state['last_update']
        # print(delta_time)
        mov1, mov2 = 0, 0
        dts = []
        
        if game_state['mov_until1'] > time.time():
            dts.append(delta_time)
        else:
            if game_state['last_update'] < game_state['mov_until1']:
                dts.append(game_state['mov_until1'] - game_state['last_update'])
            else:
                dts.append(0)

        if game_state['mov_until2'] > time.time():
            dts.append(delta_time)
        else:
            if game_state['last_update'] < game_state['mov_until2']:
                dts.append(game_state['mov_until2'] - game_state['last_update'])
            else:
                dts.append(0)

        mov1 = game_state['mov1']
        mov2 = game_state['mov2']
        players = []
        players.append(Player(distance, game_state['pos1'], pwidth, pheight, width, height, mov1, speed=200))
        players.append(Player(width - distance - pwidth, game_state['pos2'], pwidth, pheight, width, height, mov2, speed=200))
        pos_x, pos_y, vecx, vecy, p = self.simulate_ball_position(game_state['posx'], game_state['posy'], game_state['vecx'], game_state['vecy'], delta_time, players, dts)
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
                else:
                    game_state["centered"] = 0
                    game_state["start"] = time.time() + 3
            game_state["playing"] = 0
            

        game_state['last_update'] = update_time
        self.game_session.set_game_state(game_state)

    def move_up(self, player):
        game_state = self.game_session.get_game_state()
        if player == 0:
            game_state['mov1'] = -1
            game_state['mov_until1'] = time.time() + 0.25
        else:
            game_state['mov2'] = -1
            game_state['mov_until2'] = time.time() + 0.25
        self.game_session.set_game_state(game_state)


    def move_down(self, player):
        game_state = self.game_session.get_game_state()
        if player == 0:
            game_state['mov1'] = 1
            game_state['mov_until1'] = time.time() + 0.25
        else:
            game_state['mov2'] = 1
            game_state['mov_until2'] = time.time() + 0.25
        self.game_session.set_game_state(game_state)


    def get_player(self, ind):
        if ind == 1:
            player = self.game_session.player1.login if self.game_session.player1 else 'Waiting...'
        else:
            player = self.game_session.player2.login if self.game_session.player2 else 'Waiting...'
        return player
    

    def get_status(self):
        game_state = self.game_session.get_game_state()
        if self.game_session.player2 is None or self.game_session.player1 is None:
            status = "Waiting for other player"
        elif game_state['disc1'] == 1:
            status = "Waiting for player1"
        elif game_state['disc2'] == 1:
            status = "Waiting for player2"
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