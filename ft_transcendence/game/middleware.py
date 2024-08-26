

from django.utils.deprecation import MiddlewareMixin
from game.models import GameSession
from game.models import TournamentSession

class CleanupMiddleware(MiddlewareMixin):
    _initialized = False

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
        print('Cleanup complete.')