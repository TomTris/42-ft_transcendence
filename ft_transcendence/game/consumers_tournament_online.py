
import json
from channels.generic.websocket import WebsocketConsumer
from .models import GameSession, TournamentSession
from asgiref.sync import async_to_sync
import threading
import time
from users.models import MyUser
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'username', 'avatar']

mp = {}

class OnlineTournamentConsumer(WebsocketConsumer):

    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'tournament_{self.session_id}'
        self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
        if not self.game_session.is_active:
            self.close()
            return
        self.user = self.scope['user']
        if self.user in [self.tournament.player1, self.tournament.player2, self.tournament.player3, self.tournament.player4]:
            async_to_sync(self.channel_layer.group_add)(
                    self.group_name,
                    self.channel_name
                )
        else:
            self.close()

        if self.user == self.tournament.player1 and self.group_name not in mp:
            mp[self.group_name] = threading.Lock()
            self.periodic_task = threading.Thread(target=self.run, daemon=True)
            self.periodic_task.start()


    def disconnect(self, code):
        pass


    def receive(self, text_data):
        data = json.loads(text_data)
        print(data)
        self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
        game_state = self.tournament.get_tournament_state()

        with mp[self.group_name]:
            pass

    def create_games(self, game_state):
        game1 = GameSession.objects.create(
            player1=self.tournament.player1,
            player2=self.tournament.player2,
            is_tournament=True
        )
        game2 = GameSession.objects.create(
            player1=self.tournament.player3,
            player2=self.tournament.player4,
            is_tournament=True
        )
        game1.init_game_state()
        game2.init_game_state()
        self.tournament.game1 = game1
        self.tournament.game2 = game2
        game_state['start1'] = time.time() + 60
        self.tournament.save()

    def run(self):
        while 1:
            self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
            if self.tournament.is_active == False:
                break
            game_state = self.tournament.get_tournament_state()
            with mp[self.group_name]:
                if game_state['confirmed'] == 1 and self.tournament.game1 is None:
                    self.create_games(game_state)
                self.send_data_to_group()
            self.tournament.set_tournament_state(game_state)
            time.sleep(0.15)            




    def get_status(self, game_state):
        if not self.tournament.is_full():
            return 'Waiting'
        if game_state['confirmed'] == 0:
            return 'Confirming'
        if game_state['start1'] > time.time():
            return 'Starting'
        if not (self.tournament.game3 is None):
            if self.tournament.game3.is_active == False:
                return 'Finished'
        
        return 'Different'


    def get_player(self):
        if self.user == self.tournament.player1:
            return 1
        if self.user == self.tournament.player2:
            return 2
        if self.user == self.tournament.player3:
            return 3
        if self.user == self.tournament.player4:
            return 4

    def get_serialized(self, player):
        if player is None:
            return None
        serialized = UserSerializer(player)
        return serialized.data

    def send_data_to_group(self):
        game_state = self.tournament.get_tournament_state()
        message = {
            'status': self.get_status(game_state),
            'player': self.get_player(),
            'player1': self.get_serialized(self.tournament.player1),
            'player2': self.get_serialized(self.tournament.player2),
            'player3': self.get_serialized(self.tournament.player3),
            'player4': self.get_serialized(self.tournament.player4),
            'code': self.tournament.code,
            'name': self.tournament.name,
            'time': game_state['start1'] - time.time(),
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'game_update',  # Must match the method name in this consumer
                'message': message
            }
        )

    def is_user_out(self):
        player = self.get_player()
        if player == 1:
            if self.tournament.game1.is_active == False:
                if self.tournament.game1.score2 > self.tournament.game1.score1:
                    return True
        elif player == 2:
            if self.tournament.game1.is_active == False:
                if self.tournament.game1.score2 < self.tournament.game1.score1:
                    return True
        elif player == 3:
            if self.tournament.game2.is_active == False:
                if self.tournament.game1.score2 > self.tournament.game1.score1:
                    return True
        else:
            if self.tournament.game2.is_active == False:
                if self.tournament.game1.score2 < self.tournament.game1.score1:
                    return True
        return False

    def validate_message(self, message):
        if message['status'] != 'Different':
            return message
        game_state = self.tournament.get_tournament_state()
        with mp[self.group_name]:
            if self.is_user_out():
                message['status'] = 'Out'
            if game_state['start1'] < time.time():
                message['status'] = 'Joining'
                self.get_match(game_state)



    def game_update(self, event):
        game_state = self.tournament.get_tournament_state()
        self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
        message = event['message']
        self.validate_message(message)
        self.send(text_data=json.dumps(message))