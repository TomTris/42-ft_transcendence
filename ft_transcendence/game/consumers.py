import json
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import GameSession

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'game_{self.session_id}'
        self.game_session = GameSession.objects.all().get(id=self.session_id)
        user = self.scope['user']
        if user in [self.game_session.player1, self.game_session.player2]:
            self.accept()
            self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
        else:
            self.close()

    def disconnect(self, close_code):
        if self.user == self.game_session.player1 and self.game_session.player2 is None:
            self.game_session.delete()
            return
        if self.user == self.game_session.player1:
            self.game_session.player1
        else:
            pass
    

    def receive(self, text_data):
        data = json.loads(text_data)
        player1 = self.game_session.player1.login if self.game_session.player1 else 'Waiting...'
        player2 = self.game_session.player2.login if self.game_session.player2 else 'Waiting...'
        self.send(text_data=json.dumps({
            'message': 'Move received',
            'player1': player1,
            'player2': player2,
        }))