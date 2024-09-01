from django.urls import re_path
from . import consumers_remote
from . import consumers_offline
from . import consumers_tournament
from . import consumers_tournament_online
from pages.consumers import InviteConsumer
from chat.consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'^wss/game/(?P<session_id>\d+)/$', consumers_remote.GameConsumer.as_asgi()),
    re_path(r'wss/game/offline/$', consumers_offline.OfflineConsumer.as_asgi()),
    re_path(r'wss/game/bot/$', consumers_offline.AIConsumer.as_asgi()),
    re_path(r'wss/game/tournament/$', consumers_tournament.TournamentConsumer.as_asgi()),
    re_path(r'wss/game/tournament/(?P<session_id>\d+)/$', consumers_tournament_online.OnlineTournamentConsumer.as_asgi()),
    re_path(r'wss/chat/$', ChatConsumer.as_asgi()),
    re_path(r'wss/invitations/$', InviteConsumer.as_asgi()),
]