
import json
from channels.generic.websocket import WebsocketConsumer
from .models import GameSession, TournamentSession
from asgiref.sync import async_to_sync
import threading
import time
from users.models import User
from rest_framework import serializers
from chat.models import Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']


class OnlineTournamentConsumer(WebsocketConsumer):

    def save_to_crypto(self, game=0):
        from crypto.functions import add_tournament
        if game == 0:
            add_tournament(
                str(self.tournament.player1.id),
                str(self.tournament.player1.id),
                str(self.tournament.player2.id),
                str(self.tournament.player3.id),
                str(self.tournament.player4.id),
                self.tournament.game1.score1,
                self.tournament.game1.score2,
                self.tournament.game2.score1,
                self.tournament.game2.score2,
                self.tournament.game3.score1,
                self.tournament.game3.score2,
                name=self.tournament.name,
                online=1
            )

        if game == 1:
            add_tournament(
                str(self.tournament.player1.id),
                str(self.tournament.player1.id),
                str(self.tournament.player2.id),
                str(self.tournament.player3.id),
                str(self.tournament.player4.id),
                self.tournament.game1.score1,
                self.tournament.game1.score2,
                0,
                0,
                0,
                0,
                name=self.tournament.name,
                online=1
            )

        if game == 2:
            add_tournament(
                str(self.tournament.player1.id),
                str(self.tournament.player1.id),
                str(self.tournament.player2.id),
                str(self.tournament.player3.id),
                str(self.tournament.player4.id),
                0,
                0,
                self.tournament.game2.score1,
                self.tournament.game2.score2,
                0,
                0,
                name=self.tournament.name,
                online=1
            )




    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'tournament_{self.session_id}'
        self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
        if not self.tournament.is_active:
            self.close()
            return
        self.user = self.scope['user']
        if self.user in [self.tournament.player1, self.tournament.player2, self.tournament.player3, self.tournament.player4]:
            self.user.is_playing = True
            self.user.save()
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
        self.user.is_playing = False
        self.user.save()
        self.close()


    def disconnect_all(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'force_disconect',  # Must match the method name in this consumer
            }
        )


    def kick(self, event):
        self.user.is_playing = False
        self.user.save()
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
        self.user.is_playing = False
        self.user.save()
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
            self.user.is_playing = False
            self.user.save()
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

    def notify_round1(self):
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
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'chat_message',
            }
        )

    def notify_round1_start(self):
        Message.objects.create(
            send_to=self.tournament.player1.username,
            content="Your match has been started",
            game_id=self.tournament.game1.id
        )
        Message.objects.create(
            send_to=self.tournament.player2.username,
            content="Your match has been started",
            game_id=self.tournament.game1.id
        )
        Message.objects.create(
            send_to=self.tournament.player3.username,
            content="Your match has been started",
            game_id=self.tournament.game2.id
        )
        Message.objects.create(
            send_to=self.tournament.player4.username,
            content="Your match has been started",
            game_id=self.tournament.game2.id
        )
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'chat_message',
            }
        )


    def notify_round2(self, finalist1, finalist2):
        Message.objects.create(
            send_to=finalist1.username,
            content="Your match will start in a Minute"
        )
        Message.objects.create(
            send_to=finalist2.username,
            content="Your match will start in a Minute"
        )
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'chat_message',
            }
        )


    def notify_round2_start(self, finalist1, finalist2):
        Message.objects.create(
            send_to=finalist1.username,
            content="Your match has been started",
            game_id=self.tournament.game3.id
        )
        Message.objects.create(
            send_to=finalist2.username,
            content="Your match has been started",
            game_id=self.tournament.game3.id
        )
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'chat_message',
            }
        )


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
        self.tournament.save()

        self.notify_round1()

        game_state = self.tournament.get_tournament_state()
        game_state['status'] = 'Round1_count'
        game_state['game1_id'] = game1.id
        game_state['game2_id'] = game2.id

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

    def both_finished(self, game_state):
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

        
        self.notify_round2(finalist1, finalist2)
        time.sleep(3) #update to 60
        self.notify_round2_start(finalist1, finalist2)

        game_state['status'] = "Round2"
        game_state['final1'] = 1 if self.tournament.game1.score1 > self.tournament.game1.score2 else 2
        game_state['final2'] = 3 if self.tournament.game2.score1 > self.tournament.game2.score2 else 4
        game_state['game3_id'] = self.tournament.game3.id
        self.tournament.set_tournament_state(game_state)
        self.send_data_to_group()
        res = 0 
        start = time.time()
        while True:
            self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
            if  not self.tournament.game3.is_active:
                break
            if not self.tournament.game3.connected and start + 300 > time.time():
                res = 1
                break
            time.sleep(1)
        if res == 0:
            game_state['status'] = 'Finished'
            game_state['pos1'] = self.get_serialized(self.tournament.game3.player1) if self.tournament.game3.score1 > self.tournament.game3.score2 else self.get_serialized(self.tournament.game3.player2)
            game_state['pos2'] = self.get_serialized(self.tournament.game3.player2) if self.tournament.game3.score1 < self.tournament.game3.score2 else self.get_serialized(self.tournament.game3.player1)
            game_state['pos3_1'] = self.get_serialized(self.tournament.game1.player1) if self.tournament.game1.score1 < self.tournament.game1.score2 else self.get_serialized(self.tournament.game1.player2)
            game_state['pos3_2'] = self.get_serialized(self.tournament.game2.player1) if self.tournament.game2.score1 < self.tournament.game2.score2 else self.get_serialized(self.tournament.game2.player2)
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            self.save_to_crypto()
            time.sleep(30)
            self.disconnect_all()
            self.tournament.is_active = False
            self.tournament.save()
        else:
            game_state['status'] = 'Cancel'
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            self.tournament.delete()
            time.sleep(30)
            self.disconnect_all()
            self.tournament.is_active = False
            self.tournament.save()

    def one_finished(self, game_state):
        if not self.tournament.game1.connected:
            self.tournament.game1.delete()
            game_state['pos1'] = self.get_serialized(self.tournament.game2.player1) if self.tournament.game2.score1 > self.tournament.game2.score2 else self.get_serialized(self.tournament.game2.player2)
            game_state['pos2'] = self.get_serialized(self.tournament.game2.player2) if self.tournament.game2.score1 < self.tournament.game2.score2 else self.get_serialized(self.tournament.game2.player1)
            game_state['pos3_1'] = self.get_serialized(self.tournament.player1)
            game_state['pos3_2'] = self.get_serialized(self.tournament.player2)
            game_state['status'] = 'Finished'
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            self.save_to_crypto(2)
            time.sleep(30)
            self.disconnect_all()
            self.tournament.is_active = False
            self.tournament.save()

        if not self.tournament.game2.connected:
            self.tournament.game2.delete()
            game_state['pos1'] = self.get_serialized(self.tournament.game1.player1) if self.tournament.game1.score1 > self.tournament.game1.score2 else self.get_serialized(self.tournament.game1.player2)
            game_state['pos2'] = self.get_serialized(self.tournament.game1.player2) if self.tournament.game1.score1 < self.tournament.game1.score2 else self.get_serialized(self.tournament.game1.player1)
            game_state['pos3_1'] = self.get_serialized(self.tournament.player4)
            game_state['pos3_2'] = self.get_serialized(self.tournament.player3)
            game_state['status'] = 'Finished'
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            self.save_to_crypto(1)
            time.sleep(30)
            self.disconnect_all()
            self.tournament.is_active = False
            self.tournament.save()

    
    def none_finished(self, game_state):
        game_state['status'] = 'Cancel'
        self.tournament.set_tournament_state(game_state)
        self.send_data_to_group()
        self.tournament.delete()
        time.sleep(30)
        self.disconnect_all()
        self.tournament.is_active = False
        self.tournament.save()


    def start_status_updates(self):
        def status_update_loop():
            game_state = self.tournament.get_tournament_state()
            time.sleep(3) #change to 60
            
            self.notify_round1_start()

            game_state['status'] = 'Round1'
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            res = 0
            start = time.time()
            while True:
                self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
                if not self.tournament.game1.is_active and not self.tournament.game2.is_active:
                    res = 1
                    break
                if time.time() > start + 300 and (not self.tournament.game1.connected or not self.tournament.game2.connected):
                    if not self.tournament.game1.connected and not self.tournament.game2.connected:
                        break
                    res = 2
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


            if res == 1:
                self.both_finished(game_state)
            elif res == 2:
                self.one_finished(game_state)
            else:
                self.none_finished(game_state)

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
        self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
        message = event['message']
        self.validate_message(message)
        self.send(text_data=json.dumps(message))