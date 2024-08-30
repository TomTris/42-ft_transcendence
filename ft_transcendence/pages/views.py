from django.shortcuts import render, redirect
from users.models import MyUser
from django.db.models import Q
from game.models import GameSession
from crypto.functions import get_tournament_by_creator, get_tournament
from chat.serializer import UserSerializer
from users.models import MyUser
from datetime import datetime, timedelta


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


def modify_data_for_view():
    output = []
    all_tournaments = get_tournament()
    
    for tournament in all_tournaments:
        userId = tournament[0]
        try:
            user = MyUser.objects.get(id=userId)
            serializer = UserSerializer(user)
            user = serializer.data

        except MyUser.DoesNotExist:
            user = {
                'id':userId,
                'username':'Deleted',
                'avatar':'/media/default/default.png'
            }

        reference_date = datetime(1970, 1, 1)  # Unix epoch start date

        # Calculate the future date by adding the seconds
        future_date = reference_date + timedelta(seconds=tournament[3])
        
        # Extract year, month, and day from the future date
        year = future_date.year
        month = future_date.month
        day = future_date.day
        hour = future_date.hour
        minutes = future_date.minute

        data = {
            'owner':user,
            'name':tournament[1],
            'year':year,
            'month':month if month > 9 else '0' + str(month),
            'day':day,
            'hour':hour,
            'minutes':minutes,
            'online':tournament[2]
        }
        output.append(data)
    length = len(output)
    for i in range(int(length // 2)):
        output[i], output[-1 -i] = output[-1 -i], output[i]
    return output


def tournaments_view(request):
    data = {
        'tournaments' : modify_data_for_view(),
    }
    print(data)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/tournaments.html', data)
    return render(request, "tournaments.html", data)


#for test modsecurity
from django.http import HttpResponse
from django.db import connection
def vulnerable_view(request):
    query_param = request.GET.get('id', '')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM users_myuser")
    results = cursor.fetchall()
    return HttpResponse(f"Results: {results}")