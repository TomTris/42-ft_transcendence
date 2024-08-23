from django.urls import re_path
from . import consumers_remote
from . import consumers_offline
from . import consumers_tournament

websocket_urlpatterns = [
    re_path(r'^wss/game/(?P<session_id>\d+)/$', consumers_remote.GameConsumer.as_asgi()),
    re_path(r'wss/game/offline/$', consumers_offline.OfflineConsumer.as_asgi()),
    re_path(r'wss/game/bot/$', consumers_offline.AIConsumer.as_asgi()),
    re_path(r'wss/game/tournament/$', consumers_tournament.TournamentConsumer.as_asgi()),
]