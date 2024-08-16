from django.shortcuts import render, redirect, get_object_or_404
from .models import GameSession
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import GameSession
import json

@csrf_exempt
def start_or_join_game(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id', '')
            if session_id:
                game_session = get_object_or_404(GameSession, id=session_id)
                if not game_session.is_full():
                    game_session.add_player(request.user)
                    return JsonResponse({'session_id': game_session.id, 'message': 'Joined game successfully'})
                else:
                    return JsonResponse({'error': 'Game session is full'}, status=400)
            else:
                game_session = GameSession.objects.create()
                game_session.add_player(request.user)
                return JsonResponse({'session_id': game_session.id})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)


def game_state(request, session_id):
    game_session = get_object_or_404(GameSession, id=session_id)
    if request.user not in [game_session.player1, game_session.player2]:
        return JsonResponse({'error': 'Not part of this game'}, status=403)
    return JsonResponse(game_session.game_state)


def game_view(request):
    return render(request, "game.html")

def playing_view(request, session_id):

    game_session = get_object_or_404(GameSession, id=session_id)
    if request.user not in [game_session.player1, game_session.player2]:
        return redirect('game_view') 
    
    return render(request, "playing.html", {'session_id': session_id})