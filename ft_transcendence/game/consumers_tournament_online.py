
import json
from channels.generic.websocket import WebsocketConsumer
from .models import GameSession, TournamentSession


class OnlineTournamentConsumer(WebsocketConsumer):

    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'game_{self.session_id}'
        self.game_session = TournamentSession.objects.filter(id=self.session_id).first()

    def disconnect(self, code):
        pass


    def receive(self):
        pass