
import json
from channels.generic.websocket import WebsocketConsumer
from .models import GameSession, TournamentSession
from asgiref.sync import async_to_sync
import threading
import time
from users.models import User
from rest_framework import serializers
from chat.models import Message
from django.db.models import Q

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']


class OnlineTournamentConsumer(WebsocketConsumer):

    def get_newest_user(self):
        self.user = User.objects.get(id=self.user.id)

    def save_to_crypto(self, game=0):
        from crypto.functions import add_tournament
        if game == 0:
            add_tournament(
                str(self.tournament.player1.username),
                str(self.tournament.player1.username),
                str(self.tournament.player2.username),
                str(self.tournament.player3.username),
                str(self.tournament.player4.username),
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
                str(self.tournament.player1.username),
                str(self.tournament.player1.username),
                str(self.tournament.player2.username),
                str(self.tournament.player3.username),
                str(self.tournament.player4.username),
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
                str(self.tournament.player1.username),
                str(self.tournament.player1.username),
                str(self.tournament.player2.username),
                str(self.tournament.player3.username),
                str(self.tournament.player4.username),
                0,
                0,
                self.tournament.game2.score1,
                self.tournament.game2.score2,
                0,
                0,
                name=self.tournament.name,
                online=1
            )



    def send_message(self, game_state):
        mess = 'm' + str(self.get_player())
        if game_state[mess] == -1:
            m = Message.objects.create(
                send_to=self.user,
                content='Tournament',
                game_id=self.session_id
            )
            game_state[mess] = m.id
            async_to_sync(self.channel_layer.group_send)(
                'chat',
                {
                    'type': 'sending_to_one',
                    'id':self.user.id
                }
            )

    def delete_message(self):
        game_state = self.tournament.get_tournament_state()
        mess = 'm' + str(self.get_player())
        if game_state[mess] != -1:
            Message.objects.filter(id=game_state[mess]).delete()
            game_state[mess] = -1
            async_to_sync(self.channel_layer.group_send)(
                'chat',
                {
                    'type': 'sending_to_one',
                    'id':self.user.id
                }
            )
            self.tournament.set_tournament_state(game_state)



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
            self.send_message(game_state)
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
        self.get_newest_user()
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )
        self.user.is_playing = False
        self.user.save()
        self.delete_message()
        self.send_data_to_group()
        self.close()


    def disconnect_all(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'force_disconect',  # Must match the method name in this consumer
            }
        )


    def kick(self, event):
        self.get_newest_user()
        message = event['message']
        message['status'] = 'Kick'
        if message['player'] == self.get_player():
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name,
                self.channel_name
            )
            self.user.is_playing = False
            self.user.save()
            self.send(text_data=json.dumps(message))
            self.delete_message()
            if message['player'] == 2:
                self.tournament.player2 = None
            if message['player'] == 3:
                self.tournament.player3 = None
            if message['player'] == 4:
                self.tournament.player4 = None
            self.tournament.save()
            self.send_data_to_group()
            self.close()

    def handle_kick(self, player):
        self.get_newest_user()
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
        self.get_newest_user()
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )
        message = {
            'status': "Cancel"
        }
        self.send(text_data=json.dumps(message))
        self.user.is_playing = False
        self.user.save()
  
        self.close()

    
    def delete_all(self):
        game_state = self.tournament.get_tournament_state()
        for i in range(4):
            mess = 'm' + str(i + 1)
            if game_state[mess] != -1:
                Message.objects.filter(id=game_state[mess]).delete()
                if i == 0:
                    id = self.tournament.player1.id
                elif i == 1:
                    id = self.tournament.player2.id
                elif i == 2:
                    id = self.tournament.player3.id
                else:
                    id = self.tournament.player4.id

                async_to_sync(self.channel_layer.group_send)(
                    'chat',
                    {
                        'type': 'sending_to_one',
                        'id':id
                    }
                )


    def handle_cancel(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'cancel',  # Must match the method name in this consumer
            }
        )
        self.delete_all()
        self.tournament.delete()

    def quit(self, event):
        self.get_newest_user()
        message = event['message']
        if message['player'] == self.get_player():
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name,
                self.channel_name
            )
            self.user.is_playing = False
            self.user.save()
            self.delete_message()
            if message['player'] == 2:
                self.tournament.player2 = None
            if message['player'] == 3:
                self.tournament.player3 = None
            if message['player'] == 4:
                self.tournament.player4 = None
            self.tournament.save()
            self.send_data_to_group()
            self.close()
    

    def handle_quit(self, player):
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
        m1 = Message.objects.create(
            send_to=self.tournament.player1,
            content="Your match will start in a Minute"
        )
        m2 = Message.objects.create(
            send_to=self.tournament.player2,
            content="Your match will start in a Minute"
        )
        m3 = Message.objects.create(
            send_to=self.tournament.player3,
            content="Your match will start in a Minute"
        )
        m4 = Message.objects.create(
            send_to=self.tournament.player4,
            content="Your match will start in a Minute"
        )
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'sending_to_four',
                'id1': self.tournament.player1.id,
                'id2': self.tournament.player2.id,
                'id3': self.tournament.player3.id,
                'id4': self.tournament.player4.id
            }
        )
        return m1, m2, m3, m4

    def notify_round1_start(self, m1, m2, m3, m4):
        m1.delete()
        m2.delete()
        m3.delete()
        m4.delete()
        m1 = Message.objects.create(
            send_to=self.tournament.player1,
            content="Your match has been started",
            game_id=self.tournament.game1.id
        )
        m2 = Message.objects.create(
            send_to=self.tournament.player2,
            content="Your match has been started",
            game_id=self.tournament.game1.id
        )
        m3 = Message.objects.create(
            send_to=self.tournament.player3,
            content="Your match has been started",
            game_id=self.tournament.game2.id
        )
        m4 = Message.objects.create(
            send_to=self.tournament.player4,
            content="Your match has been started",
            game_id=self.tournament.game2.id
        )
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'sending_to_four',
                'id1': self.tournament.player1.id,
                'id2': self.tournament.player2.id,
                'id3': self.tournament.player3.id,
                'id4': self.tournament.player4.id
            }
        )
        return m1, m2, m3, m4
    

    def notify_round2(self, finalist1, finalist2):

        m1 = Message.objects.create(
            send_to=finalist1,
            content="Your match will start in a Minute"
        )
        m2 = Message.objects.create(
            send_to=finalist2,
            content="Your match will start in a Minute"
        )
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'sending_to_two',
                'id1': finalist1.id,
                'id2': finalist2.id
            }
        )
        return m1, m2


    def notify_round2_start(self, finalist1, finalist2, m1, m2):
        m1.delete()
        m2.delete()
        m1 = Message.objects.create(
            send_to=finalist1,
            content="Your match has been started",
            game_id=self.tournament.game3.id
        )
        m2 = Message.objects.create(
            send_to=finalist2,
            content="Your match has been started",
            game_id=self.tournament.game3.id
        )
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'sending_to_two',
                'id1': finalist1.id,
                'id2': finalist2.id,
            }
        )
        return m1, m2


    def create_games(self):
        game1 = GameSession.objects.create(
            player1=self.tournament.player1,
            player2=self.tournament.player2,
            is_tournament=True,
            tournament_id=self.tournament.id
        )
        game2 = GameSession.objects.create(
            player1=self.tournament.player3,
            player2=self.tournament.player4,
            is_tournament=True,
            tournament_id=self.tournament.id
        )
        game1.init_game_state()
        game2.init_game_state()
        self.tournament.game1 = game1
        self.tournament.game2 = game2
        self.tournament.save()

        game_state = self.tournament.get_tournament_state()
        game_state['status'] = 'Round1_count'
        game_state['game1_id'] = game1.id
        game_state['game2_id'] = game2.id
        game_state['start'] = time.time() + 30

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
        game_state['start'] = time.time() + 30
        self.tournament.set_tournament_state(game_state)
        self.send_data_to_group()
        finalist1 = self.get_finalist(1)
        finalist2 = self.get_finalist(2)
        game3 = GameSession.objects.create(
            player1=finalist1,
            player2=finalist2,
            is_tournament=True,
            tournament_id=self.tournament.id
        )
        game3.init_game_state()
        self.tournament.game3 = game3
        self.tournament.save()

        m1, m2 = self.notify_round2(finalist1, finalist2)
        time.sleep(30) #update to 60
        m1, m2 = self.notify_round2_start(finalist1, finalist2, m1, m2)
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
            if not self.tournament.game3.connected and start + 300 < time.time():
                res = 1
                break
            time.sleep(1)
        m1.delete()
        m2.delete()
        # print('222222222222222222222222222222')
        # print('222222222222222222222222222222')
        # print(self.tournament.player1.is_playing)
        # print(self.tournament.player2.is_playing)
        # print(self.tournament.player3.is_playing)
        # print(self.tournament.player4.is_playing)
        # print('222222222222222222222222222222')
        # print('222222222222222222222222222222')


        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'sending_to_two',
                'id1': finalist1.id,
                'id2': finalist2.id,
            }
        )
        # print('res', res)
        if res == 0:
            
            game_state['status'] = 'Finished'
            game_state['pos1'] = self.get_serialized(self.tournament.game3.player1) if self.tournament.game3.score1 > self.tournament.game3.score2 else self.get_serialized(self.tournament.game3.player2)
            game_state['pos2'] = self.get_serialized(self.tournament.game3.player2) if self.tournament.game3.score1 < self.tournament.game3.score2 else self.get_serialized(self.tournament.game3.player1)
            game_state['pos3_1'] = self.get_serialized(self.tournament.game1.player1) if self.tournament.game1.score1 < self.tournament.game1.score2 else self.get_serialized(self.tournament.game1.player2)
            game_state['pos3_2'] = self.get_serialized(self.tournament.game2.player1) if self.tournament.game2.score1 < self.tournament.game2.score2 else self.get_serialized(self.tournament.game2.player2)
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            self.save_to_crypto()
            # print('111111111111111111111')
            self.tournament.player1.is_playing = False
            # print(self.tournament.player1.is_playing)
            self.tournament.player2.is_playing = False
            # print(self.tournament.player2.is_playing)
            self.tournament.player3.is_playing = False
            # print(self.tournament.player3.is_playing)
            self.tournament.player4.is_playing = False
            # print(self.tournament.player4.is_playing)
            # print(self.tournament.player1.email)
            # print(self.tournament.player2.email)
            # print(self.tournament.player3.email)
            # print(self.tournament.player4.email)
            # print('111111111111111111111')
            self.tournament.player1.save()
            self.tournament.player2.save()
            self.tournament.player3.save()
            self.tournament.player4.save()
            self.delete_all()
            self.tournament.finished = True
            self.tournament.save()

            Message.objects.filter(Q(send_to=self.tournament.player1) | Q(send_to=self.tournament.player2) | Q(send_to=self.tournament.player3) | Q(send_to=self.tournament.player4), sender=None).delete()
            async_to_sync(self.channel_layer.group_send)(
                'chat',
                {
                    'type': 'sending_to_four',
                    'id1': self.tournament.player1.id,
                    'id2': self.tournament.player2.id,
                    'id3': self.tournament.player3.id,
                    'id4': self.tournament.player4.id
                }
            )
            time.sleep(30)
            self.tournament.is_active = False
            self.tournament.save()
            self.disconnect_all()
            
        else:
            game3.delete()
            game_state['status'] = 'Cancel'
            self.tournament.player1.is_playing = False
            self.tournament.player2.is_playing = False
            self.tournament.player3.is_playing = False
            self.tournament.player4.is_playing = False
            self.tournament.player1.save()
            self.tournament.player2.save()
            self.tournament.player3.save()
            self.tournament.player4.save()
            self.delete_all()
            async_to_sync(self.channel_layer.group_send)(
                'chat',
                {
                    'type': 'sending_to_four',
                    'id1': self.tournament.player1.id,
                    'id2': self.tournament.player2.id,
                    'id3': self.tournament.player3.id,
                    'id4': self.tournament.player4.id
                }
            )
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            self.tournament.delete()
            time.sleep(30)
            self.disconnect_all()


    def one_finished(self, game_state, m1, m2, m3, m4):
        if not self.tournament.game1.connected:
            self.tournament.game1.delete()
            m1.delete()
            m2.delete()
            async_to_sync(self.channel_layer.group_send)(
                'chat',
                {
                    'type': 'sending_to_four',
                    'id1': self.tournament.player1.id,
                    'id2': self.tournament.player2.id,
                    'id3': self.tournament.player3.id,
                    'id4': self.tournament.player4.id
                }
            )
            game_state['pos1'] = self.get_serialized(self.tournament.game2.player1) if self.tournament.game2.score1 > self.tournament.game2.score2 else self.get_serialized(self.tournament.game2.player2)
            game_state['pos2'] = self.get_serialized(self.tournament.game2.player2) if self.tournament.game2.score1 < self.tournament.game2.score2 else self.get_serialized(self.tournament.game2.player1)
            game_state['pos3_1'] = self.get_serialized(self.tournament.player1)
            game_state['pos3_2'] = self.get_serialized(self.tournament.player2)
            game_state['status'] = 'Finished'
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            self.save_to_crypto(2)
            self.tournament.player1.is_playing = False
            self.tournament.player2.is_playing = False
            self.tournament.player3.is_playing = False
            self.tournament.player4.is_playing = False
            self.tournament.player1.save()
            self.tournament.player2.save()
            self.tournament.player3.save()
            self.tournament.player4.save()
            self.delete_all()
            Message.objects.filter(Q(send_to=self.tournament.player1) | Q(send_to=self.tournament.player2) | Q(send_to=self.tournament.player3) | Q(send_to=self.tournament.player4), sender=None).delete()
            async_to_sync(self.channel_layer.group_send)(
                'chat',
                {
                    'type': 'sending_to_four',
                    'id1': self.tournament.player1.id,
                    'id2': self.tournament.player2.id,
                    'id3': self.tournament.player3.id,
                    'id4': self.tournament.player4.id
                }
            )
            time.sleep(30)
            self.disconnect_all()
            self.tournament.is_active = False
            self.tournament.save()

        if not self.tournament.game2.connected:
            self.tournament.game2.delete()
            m3.delete()
            m4.delete()
            async_to_sync(self.channel_layer.group_send)(
                'chat',
                {
                    'type': 'sending_to_four',
                    'id1': self.tournament.player1.id,
                    'id2': self.tournament.player2.id,
                    'id3': self.tournament.player3.id,
                    'id4': self.tournament.player4.id
                }
            )
            game_state['pos1'] = self.get_serialized(self.tournament.game1.player1) if self.tournament.game1.score1 > self.tournament.game1.score2 else self.get_serialized(self.tournament.game1.player2)
            game_state['pos2'] = self.get_serialized(self.tournament.game1.player2) if self.tournament.game1.score1 < self.tournament.game1.score2 else self.get_serialized(self.tournament.game1.player1)
            game_state['pos3_1'] = self.get_serialized(self.tournament.player4)
            game_state['pos3_2'] = self.get_serialized(self.tournament.player3)
            game_state['status'] = 'Finished'
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            self.save_to_crypto(1)
            self.tournament.player1.is_playing = False
            self.tournament.player2.is_playing = False
            self.tournament.player3.is_playing = False
            self.tournament.player4.is_playing = False
            self.tournament.player1.save()
            self.tournament.player2.save()
            self.tournament.player3.save()
            self.tournament.player4.save()
            self.delete_all()
            Message.objects.filter(Q(send_to=self.tournament.player1) | Q(send_to=self.tournament.player2) | Q(send_to=self.tournament.player3) | Q(send_to=self.tournament.player4), sender=None).delete()
            async_to_sync(self.channel_layer.group_send)(
                'chat',
                {
                    'type': 'sending_to_four',
                    'id1': self.tournament.player1.id,
                    'id2': self.tournament.player2.id,
                    'id3': self.tournament.player3.id,
                    'id4': self.tournament.player4.id
                }
            )
            time.sleep(30)
            self.disconnect_all()
            self.tournament.is_active = False
            self.tournament.save()

    
    def none_finished(self, game_state, m1, m2, m3, m4):
        m1.delete()
        m2.delete()
        m3.delete()
        m4.delete()
        game_state['status'] = 'Cancel'
        self.tournament.set_tournament_state(game_state)
        self.send_data_to_group()
        self.tournament.player1.is_playing = False
        self.tournament.player2.is_playing = False
        self.tournament.player3.is_playing = False
        self.tournament.player4.is_playing = False
        self.tournament.player1.save()
        self.tournament.player2.save()
        self.tournament.player3.save()
        self.tournament.player4.save()
        self.delete_all()
        Message.objects.filter(Q(send_to=self.tournament.player1) | Q(send_to=self.tournament.player2) | Q(send_to=self.tournament.player3) | Q(send_to=self.tournament.player4), sender=None).delete()
        async_to_sync(self.channel_layer.group_send)(
            'chat',
            {
                'type': 'sending_to_four',
                'id1': self.tournament.player1.id,
                'id2': self.tournament.player2.id,
                'id3': self.tournament.player3.id,
                'id4': self.tournament.player4.id
            }
        )
        self.tournament.delete()
        time.sleep(30)
        self.disconnect_all()
        self.tournament.is_active = False
        self.tournament.save()


    def start_status_updates(self):
        def status_update_loop():

            m1, m2, m3, m4 = self.notify_round1()
            game_state = self.tournament.get_tournament_state()

            time.sleep(30) #change to 60
            
            m1, m2, m3, m4 = self.notify_round1_start(m1, m2, m3, m4)

            game_state['status'] = 'Round1'
            self.tournament.set_tournament_state(game_state)
            self.send_data_to_group()
            res = 0
            start = time.time()
            while True:
                self.tournament = TournamentSession.objects.filter(id=self.session_id).first()
                if game_state['finished1'] == 0 and not self.tournament.game1.is_active:
                    game_state['finished1'] = 1
                    self.tournament.set_tournament_state(game_state)
                    self.send_data_to_group()
                    m1.delete()
                    m2.delete()
                    async_to_sync(self.channel_layer.group_send)(
                        'chat',
                        {
                            'type': 'sending_to_two',
                            'id1': self.tournament.player1.id,
                            'id2': self.tournament.player2.id,
                        }
                    )
                if game_state['finished2'] == 0 and not self.tournament.game2.is_active:
                    game_state['finished2'] = 1
                    self.tournament.set_tournament_state(game_state)
                    self.send_data_to_group()
                    m3.delete()
                    m4.delete()
                    async_to_sync(self.channel_layer.group_send)(
                        'chat',
                        {
                            'type': 'sending_to_two',
                            'id1': self.tournament.player3.id,
                            'id2': self.tournament.player4.id,
                        }
                    )
                if not self.tournament.game1.is_active and not self.tournament.game2.is_active:
                    res = 1
                    break
                if time.time() > start + 300 and (not self.tournament.game1.connected or not self.tournament.game2.connected):
                    if not self.tournament.game1.connected and not self.tournament.game2.connected:
                        break
                    res = 2
                    break
                time.sleep(1)


            if res == 1:
                self.both_finished(game_state)
            elif res == 2:
                self.one_finished(game_state, m1, m2, m3, m4)
            else:
                self.none_finished(game_state, m1, m2, m3, m4)

        self.status_thread = threading.Thread(target=status_update_loop)
        self.status_thread.daemon = True
        self.status_thread.start()


    def receive(self, text_data):
        data = json.loads(text_data)
        self.get_newest_user()
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
            'start':int(game_state['start'] - time.time())
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