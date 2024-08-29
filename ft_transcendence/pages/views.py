from django.shortcuts import render, redirect
from users.models import MyUser
from django.db.models import Q
from game.models import GameSession
from crypto.functions import get_tournaments, get_tournament_by_creator

def home_view(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/home.html')
    return render(request, "home.html")

def inactive_view(request):
    return render(request, "inactive.html")

def best_view(request):
    return render(request, "index.html")

def users_view(request):
    users = MyUser.objects.order_by("id")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/users.html', {'users':users, 'amount':len(users)})
    return render(request, "users.html", {'users':users, 'amount':len(users)})

def user_view(request, id): 
    user = MyUser.objects.all().filter(id=id).first()
    if not user:
        return render(request, "user_doesnt_exist.html")
    matches = GameSession.objects.filter(Q(player1=user) | Q(player2=user))
    matches_with_ids = []
    for match in matches:
        if match.player1 == user:
            match_data = {
                'match': match,
                'player1': user,
                'player2': match.player2,
            }
        else:
            match_data = {
                'match': match,
                'player1': match.player1,
                'player2': user,
            }
            
        matches_with_ids.append(match_data)
    if user.total == 0:
        winrate = 0
    else:
        winrate = "%.2f" % (user.wins / user.total)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/user.html', {'user':user, "matches_with_ids":matches_with_ids, 'winrate':winrate})
    return render(request, "user.html", {'user':user, "matches_with_ids":matches_with_ids, 'winrate':winrate})


def modify_data_for_view(tournaments):
    pass


def tournaments_view(request):
    tournaments = get_tournaments()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/user.html', )
    return render(request, "user.html", )


#for test modsecurity
from django.http import HttpResponse
from django.db import connection
def vulnerable_view(request):
    query_param = request.GET.get('id', '')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM users_myuser")
    results = cursor.fetchall()
    return HttpResponse(f"Results: {results}")