import json
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import GameSession
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
from .models import width, height, pwidth, pheight, radius, distance

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'game_{self.session_id}'
        self.game_session = GameSession.objects.filter(id=self.session_id).first()
        if self.game_session is None:
            self.close()
            return
        self.user = self.scope['user']
        if self.user in [self.game_session.player1, self.game_session.player2]:
            self.accept()
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
            if self.user == self.game_session.player1:
                self.game_session.game_state['disc1'] = 0
            else:
                self.game_session.game_state['disc2'] = 0
            if self.game_session.game_state['disc1'] == 0 and self.game_session.game_state['disc2'] == 0:
                self.game_session.game_state['start'] = time.time() + 4
            self.game_session.save()
        else:
            self.close()

    def disconnect(self, close_code):
        
        if self.game_session is None:
            return

        if self.user == self.game_session.player1:
            if self.game_session.player2 is None:
                self.game_session.delete()
                return
            self.game_session.game_state['disc1'] = 1
        else:
            self.game_session.game_state['disc2'] = 1
        self.game_session.game_state['start'] = time.time() + 21
        self.game_session.save()
        if self.game_session.game_state['disc1'] == 1 and self.game_session.game_state['disc2'] == 1:
            self.game_session.delete()
            return
        
        self.send_data_to_group()
    

    def receive(self, text_data):
        self.game_session = GameSession.objects.filter(id=self.session_id).first()
        if self.game_session is None:
            return
        data = json.loads(text_data)
        self.game_session.update_playing()
        if self.game_session.game_state['centered'] == 0:
            self.game_session.position_center_random_move()
        elif self.game_session.game_state['playing']:
            self.game_session.make_move()
        self.send_data_to_group()
    

    def get_player(self, ind):
        if ind == 1:
            player = self.game_session.player1.login if self.game_session.player1 else 'Waiting...'
        else:
            player = self.game_session.player2.login if self.game_session.player2 else 'Waiting...'
        return player
    

    def get_status(self):
        if self.game_session.player2 is None or self.game_session.player1 is None:
            status = "Waiting for other player"
        elif self.game_session.game_state['disc1'] == 1:
            status = "Waiting for player1"
        elif self.game_session.game_state['disc2'] == 1:
            status = "Waiting for player2"
        elif self.game_session.game_state['start'] - time.time() >= 0.0:
            status = "Count down"
        else:
            status = "Playing"
        return status
    
    
    def get_time(self):
        return int(self.game_session.game_state['start'] - time.time())

    
    def send_data_to_group(self):
        message = {
                'status':self.get_status(),
                'player1':self.get_player(1),
                'player2':self.get_player(2),
                'pos1':self.game_session.game_state['pos1'],
                'pos2':self.game_session.game_state['pos2'],
                'posx':self.game_session.game_state['posx'],
                'posy':self.game_session.game_state['posy'],
                'pheight': pheight,
                'pwidth': pwidth,
                'radius': radius,
                'width': width,
                'height': height,
                'vecy': self.game_session.game_state['vecy'],
                'vecx': self.game_session.game_state['vecx'],
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