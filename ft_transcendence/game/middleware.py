

from django.utils.deprecation import MiddlewareMixin
from game.models import GameSession
from game.models import TournamentSession
from django.conf import settings
from users.models import User


class CleanupMiddleware(MiddlewareMixin):
    _initialized = settings.INITIALIZED_1

    def process_request(self, request):
        if not self.__class__._initialized:
            self.__class__._initialized = True
            self.cleanup_unfinished_sessions()

    def cleanup_unfinished_sessions(self):
        print('Cleaning up unfinished game sessions...')
        un_finished = GameSession.objects.filter(is_active=True)
        un_finished.delete()
        un_finished = TournamentSession.objects.filter(is_active=True)
        un_finished.delete()
        users = User.objects.all()
        for user in users:
            user.is_online = False
            user.is_playing = False
            user.save()
        print('Cleanup complete.')

        
