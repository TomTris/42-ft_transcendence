from django.shortcuts import render, redirect
from users.models import MyUser
from users.models import Match
from django.db.models import Q

def home_view(request):
    return render(request, "home.html")

def inactive_view(request):
    return render(request, "inactive.html")

def best_view(request):
    return render(request, "index.html")

def users_view(request):
    users = MyUser.objects.order_by("id")
    return render(request, "users.html", {'users':users, 'amount':len(users)})

def user_view(request, id):
    id -= 1
    users = MyUser.objects.all()
    if id >= len(users) or id < 0:
        return render(request, "user_doesnt_exist.html")
    user = users[id]
    matches = Match.objects.filter(Q(player1=user.login) | Q(player2=user.login))
    matches_with_ids = []
    for match in matches:
        if match.player1 == user.login:
            match_data = {
                'match': match,
                'player1': user,
                'player2': users.get(login=match.player2),
            }
        else:
            match_data = {
                'match': match,
                'player1': users.get(login=match.player1),
                'player2': user,
            }
            
        matches_with_ids.append(match_data)
    if user.total == 0:
        winrate = 0
    else:
        winrate = "%.2f" % (user.wins / user.total)
    return render(request, "user.html", {'user':user, "matches_with_ids":matches_with_ids, 'winrate':winrate})