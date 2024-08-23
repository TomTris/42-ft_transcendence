from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_view),
    path('<int:session_id>/', views.playing_view),
    path('join-game-session/', views.join_game_session, name='join_game_session'),
    path('offline/', views.offline_view),
    path('bot/', views.bot_view),
    path('tournament/', views.tournament_view),
]
