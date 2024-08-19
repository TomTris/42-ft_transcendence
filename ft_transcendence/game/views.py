from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import GameSession
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@require_POST
def join_game_session(request):
    user = request.user
    
    game_session = GameSession.objects.filter(
        Q(player1=user) | Q(player2=user),
        is_active=True
    ).first()
    if game_session is None:
        game_session = GameSession.objects.filter(is_active=True).first()
        if game_session is None:
            game_session = GameSession.objects.create()
        try:
            game_session.add_player(user)
        except ValueError:
            return JsonResponse({'error': 'Game session is full'}, status=400)

    return JsonResponse({
        'session_id': game_session.id
    })

def game_view(request):
    return render(request, "game.html")

def playing_view(request, session_id):
    return render(request, "playing.html", {'session_id':session_id})