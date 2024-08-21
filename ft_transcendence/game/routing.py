from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^wss/game/(?P<session_id>\d+)/$', consumers.GameConsumer.as_asgi()),
]