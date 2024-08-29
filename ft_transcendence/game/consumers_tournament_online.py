
import json
from channels.generic.websocket import WebsocketConsumer
from .models import GameSession, TournamentSession
from asgiref.sync import async_to_sync
import threading
import time
from users.models import MyUser
from rest_framework import serializers
from chat.models import Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'username', 'avatar']


class OnlineTournamentConsumer(WebsocketConsumer):

    def save_to_crypto(self):
        pass



    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'tournament_{self.session_id}'
        self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
        if not self.tournament.is_active:
            self.close()
            return
        self.user = self.scope['user']
        if self.user in [self.tournament.player1, self.tournament.player2, self.tournament.player3, self.tournament.player4]:
            self.accept()
            async_to_sync(self.channel_layer.group_add)(
                    self.group_name,
                    self.channel_name
                )
            game_state = self.tournament.get_tournament_state()
            if self.tournament.is_full() and game_state['status'] == 'Waiting':
                game_state['status'] = 'Confirming'
                self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
        else:
            self.close()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )


    def force_disconect(self, event):
        self.close()


    def disconnect_all(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'force_disconect',  # Must match the method name in this consumer
            }
        )


    def kick(self, event):
        message = event['message']
        message['status'] = 'Kick'
        if message['player'] == self.get_player():
            self.send(text_data=json.dumps(message))
            self.close()

    def handle_kick(self, player):
        if player == 2:
            self.tournament.player2 = None
        if player == 3:
            self.tournament.player3 = None
        if player == 4:
            self.tournament.player4 = None
        self.tournament.save()
        message = {
            'player': player,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'kick',  # Must match the method name in this consumer
                'message': message
            }
        )
        game_state = self.tournament.get_tournament_state()
        if not self.tournament.is_full() and game_state['status'] == 'Confirming':
            game_state['status'] = 'Waiting'
            self.tournament.set_tournament_state(game_state)

    def cancel(self, event):
        message = {
            'status': "Cancel"
        }
        self.send(text_data=json.dumps(message))
        self.close()


    def handle_cancel(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'cancel',  # Must match the method name in this consumer
            }
        )
        self.tournament.delete()

    def quit(self, event):
        message = event['message']
        if message['player'] == self.get_player():
            self.close()
    

    def handle_quit(self, player):
        if player == 2:
            self.tournament.player2 = None
        if player == 3:
            self.tournament.player3 = None
        if player == 4:
            self.tournament.player4 = None
        self.tournament.save()
        message = {
            'player': player,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'quit',  # Must match the method name in this consumer
                'message': message
            }
        )
        game_state = self.tournament.get_tournament_state()
        if not self.tournament.is_full() and game_state['status'] == 'Confirming':
            game_state['status'] = 'Waiting'
            self.tournament.set_tournament_state(game_state)


    def create_games(self):
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
        Message.objects.create(
            send_to=self.tournament.player1.username,
            content="Your match will start in a Minute"
        )
        Message.objects.create(
            send_to=self.tournament.player2.username,
            content="Your match will start in a Minute"
        )
        Message.objects.create(
            send_to=self.tournament.player3.username,
            content="Your match will start in a Minute"
        )
        Message.objects.create(
            send_to=self.tournament.player4.username,
            content="Your match will start in a Minute"
        )
        self.tournament.save()
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'chat_message',
            }
        )
        game_state = self.tournament.get_tournament_state()
        game_state['status'] = 'Round1_count'
        game_state['game1_id'] = game1.id
        game_state['game2_id'] = game2.id
        print(game1.id)
        print(game2.id)
        print(game_state)
        self.tournament.set_tournament_state(game_state)
        self.send_data_to_group()
        self.start_status_updates()

    def get_finalist(self, match):
        if match == 1:
            if self.tournament.game1.score1 > self.tournament.game1.score2:
                return self.tournament.game1.player1
            return self.tournament.game1.player2
        else:
            if self.tournament.game2.score1 > self.tournament.game2.score2:
                return self.tournament.game2.player1
            return self.tournament.game2.player2


    def start_status_updates(self):
        def status_update_loop():
            game_state = self.tournament.get_tournament_state()
            time.sleep(3)
            game_state['status'] = 'Round1'
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            while True:
                self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
                if not self.tournament.game1.is_active and not self.tournament.game2.is_active:
                    break
                if game_state['finished1'] == 0 and not self.tournament.game1.is_active:
                    game_state['finished1'] = 1
                    self.tournament.set_tournament_state(game_state)
                    self.send_data_to_group()
                if game_state['finished2'] == 0 and not self.tournament.game2.is_active:
                    game_state['finished2'] = 1
                    self.tournament.set_tournament_state(game_state)
                    self.send_data_to_group()
                time.sleep(1)
            game_state['finished1'] = 1
            game_state['finished2'] = 1
            game_state['status'] = 'Round2_count'
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            finalist1 = self.get_finalist(1)
            finalist2 = self.get_finalist(2)
            game3 = GameSession.objects.create(
                player1=finalist1,
                player2=finalist2,
                is_tournament=True
            )
            game3.init_game_state()
            self.tournament.game3 = game3
            self.tournament.save()

            time.sleep(3)
            game_state['status'] = "Round2"
            game_state['final1'] = 1 if self.tournament.game1.score1 > self.tournament.game1.score2 else 2
            game_state['final2'] = 3 if self.tournament.game2.score1 > self.tournament.game2.score2 else 4
            game_state['game3_id'] = self.tournament.game3.id
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            while True:
                self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
                if  not self.tournament.game3.is_active:
                    break
                time.sleep(1)
            game_state['status'] = 'Finished'
            game_state['pos1'] = self.get_serialized(self.tournament.game3.player1) if self.tournament.game3.score1 > self.tournament.game3.score2 else self.get_serialized(self.tournament.game3.player2)
            game_state['pos2'] = self.get_serialized(self.tournament.game3.player2) if self.tournament.game3.score1 < self.tournament.game3.score2 else self.get_serialized(self.tournament.game3.player1)
            game_state['pos3_1'] = self.get_serialized(self.tournament.game1.player1) if self.tournament.game1.score1 < self.tournament.game1.score2 else self.get_serialized(self.tournament.game1.player2)
            game_state['pos3_2'] = self.get_serialized(self.tournament.game2.player1) if self.tournament.game2.score1 < self.tournament.game2.score2 else self.get_serialized(self.tournament.game2.player2)
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            self.save_to_crypto()
            time.sleep(300)
            self.disconnect_all()
            self.tournament.is_active = False
            self.tournament.save()

        self.status_thread = threading.Thread(target=status_update_loop)
        self.status_thread.daemon = True
        self.status_thread.start()


    def receive(self, text_data):
        data = json.loads(text_data)
        self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
        if data['type'] == 'kick':
            self.handle_kick(data['player'])
            self.send_data_to_group()
        elif data['type'] == 'cancel':
            self.handle_cancel()
        elif data['type'] == 'quit':
            self.handle_quit(data['player'])
            self.send_data_to_group()
        elif data['type'] == 'start':
            self.create_games()


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
            'status': game_state['status'],
            'player1': self.get_serialized(self.tournament.player1),
            'player2': self.get_serialized(self.tournament.player2),
            'player3': self.get_serialized(self.tournament.player3),
            'player4': self.get_serialized(self.tournament.player4),
            'code': self.tournament.code,
            'name': self.tournament.name,
            'game1_id': game_state['game1_id'],
            'game2_id': game_state['game2_id'],
            'finished1': game_state['finished1'],
            'finished2': game_state['finished2'],
            'final1': game_state['final1'],
            'final2': game_state['final2'],
            'game3_id': game_state['game3_id'],
            'pos1': game_state['pos1'],
            'pos2': game_state['pos2'],
            'pos3_1': game_state['pos3_1'],
            'pos3_2': game_state['pos3_2'],

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
        message['player'] = self.get_player()


    def game_update(self, event):
        game_state = self.tournament.get_tournament_state()
        self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
        message = event['message']
        self.validate_message(message)
        self.send(text_data=json.dumps(message))