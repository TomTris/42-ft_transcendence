import json
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import GameSession

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.game_session = GameSession.objects.get(id=self.session_id)
        
        user = self.scope['user']
        if not isinstance(user, AnonymousUser) and user in [self.game_session.player1, self.game_session.player2]:
            self.accept()
        else:
            self.close()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        data = json.loads(text_data)
        # Handle incoming data and update game state
        self.send(text_data=json.dumps({
            'message': 'Move received'
        }))