

from django.utils.deprecation import MiddlewareMixin
from game.models import GameSession
from game.models import TournamentSession
from chat.models import Message
from django.conf import settings
from users.models import User
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser



class CleanupMiddleware(MiddlewareMixin):
    _initialized = settings.INITIALIZED_1

    def process_request(self, request):
        user = request.user
        # print(user)
        if not isinstance(user, AnonymousUser):
            if user.is_playing == True:
                # print(user)
                # print(user.is_playing)
                t = TournamentSession.objects.filter(Q(player1=user, finished=False) | Q(player2=user, finished=False) | Q(player3=user, finished=False) | Q(player4=user, finished=False)).first()
                g = GameSession.objects.filter(Q(player1=user, is_active=True) | Q(player2=user, is_active=True)).first()
                if t is None and g is None:
                    user.is_playing = False
                    user.save()
                # print(user.is_playing)
                # print('11111121212121212')
            # if user.is_playing == False:
            #     Message.objects.filter(sender=None, send_to=user).delete()
        # print('92929292929292922')
        if not self.__class__._initialized:
            self.__class__._initialized = True
            self.cleanup_unfinished_sessions()

    def cleanup_unfinished_sessions(self):
        print('Cleaning up unfinished game sessions...')
        un_finished = GameSession.objects.filter(is_active=True)
        un_finished.delete()
        un_finished = TournamentSession.objects.filter(is_active=True)
        un_finished.delete()
        Message.objects.filter(sender=None).delete()
        users = User.objects.all()
        for user in users:
            user.is_online = False
            user.is_playing = False
            user.save()
        print('Cleanup complete.')

