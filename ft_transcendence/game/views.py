from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import GameSession
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TournamentSession
import string
import random
import json


@require_POST
def join_game_session(request):
    user = request.user
    game_session = GameSession.objects.filter(
        Q(player1=user) | Q(player2=user),
        is_active=True
    ).first()
    if game_session is None:
        game_session = GameSession.objects.filter(player2=None, is_active=True).first()
        if game_session is None:
            game_session = GameSession.objects.create()
            game_session.init_game_state()
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
    game_session = GameSession.objects.filter(id=session_id).first()
    user = request.user
    if game_session is None or user not in [game_session.player1, game_session.player2] or not game_session.is_active:
        return render(request, "user_doesnt_exist.html")
    return render(request, "play3d/play3d.html", {'session_id':session_id})

def offline_view(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/offline.html')
    return render(request, 'offline.html')

def bot_view(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/playing_bot.html')
    return render(request, 'playing_bot.html')

def tournament_view(request):
    return render(request, 'tournaments.html')

def online_tournament_view(request):
    return render(request, 'online_tournament.html')


def online_tournaments_view(request, session_id):
    user = request.user
    tournament = TournamentSession.objects.filter(id=session_id).first()
    if tournament is None or user not in [tournament.player1, tournament.player2, tournament.player3, tournament.player4]:
        return render(request, "user_doesnt_exist.html")
    return render(request, 'online_tournaments.html', {'session_id': session_id})



def generate_unique_code():
    length = 8
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if not TournamentSession.objects.filter(code=code).exists():
            return code

@require_POST
def create_tournament(request):
    name = request.POST.get('name')
    if not name:
        return JsonResponse({'error': 'Tournament name is required'}, status=400)

    code = generate_unique_code()
    tournament = TournamentSession.objects.create(name=name, code=code)
    tournament.init_tournament_state()
    tournament.add_player(request.user)
    return JsonResponse({'success': True, 'code': code, 'id':tournament.id})

@require_POST
def join_tournament(request):
    code = request.POST.get('code')
    if not code:
        return JsonResponse({'error': 'Tournament code is required'}, status=400)
    try:
        tournament = TournamentSession.objects.get(code=code, is_active=True)
        if not tournament.is_player_in(request.user):
            tournament.add_player(request.user)
        return JsonResponse({'success': True, 'id': tournament.id})
    except TournamentSession.DoesNotExist:
        return JsonResponse({'error': 'Tournament not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Tournament is full'}, status=400)