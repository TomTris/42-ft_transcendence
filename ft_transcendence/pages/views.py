from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.db.models import Q
from game.models import GameSession
from crypto.functions import get_tournament_by_creator, get_tournament
from chat.serializer import UserSerializer
from users.models import User, Friendship
from game.models import GameSession
from datetime import datetime, timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Invite
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView


def get_friend_status(current_user, user):
    if user == current_user:
        return 0
    f = Friendship.objects.filter(Q(person1=current_user, person2=user) | Q(person1=user, person2=current_user)).first()
    if f is None:
        f = Invite.objects.filter(sender=user, send_to=current_user, invite_type=1).first()
        if f is not None:
            return 3
        f = Invite.objects.filter(sender=current_user, send_to=user, invite_type=1).first()
        if f is not None:
            return 4
        return 1
    return 2


def get_invite_status(current_user, user):
    if user == current_user:
        return 0
    game = GameSession.objects.filter(Q(player1=current_user, player2=user) | Q(player1=user, player2=current_user), is_active=True).first()
    if game is not None:
        return 2
    f = Invite.objects.filter(sender=user, send_to=current_user, invite_type=2).first()
    if f is not None:
        return 3
    f = Invite.objects.filter(sender=current_user, send_to=user, invite_type=2).first()
    if f is not None:
        return 4
    return 1


def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'partials/home.html')
    return render(request, "home.html")

def inactive_view(request):
    return render(request, "inactive.html")

def best_view(request):
    return render(request, "index.html")

def users_view(request):
    users = User.objects.order_by("id")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/users.html', {'friends':users})
    return render(request, "users.html", {'friends':users})

def user_view(request, id):
    curent_user = request.user
    user = User.objects.all().filter(id=id).first()
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

    print(1)
    friend=get_friend_status(curent_user, user)
    invite = get_invite_status(curent_user, user)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/user.html', {'user':user, "matches_with_ids":matches_with_ids, 'winrate':winrate, 'friend':friend, 'invite':invite})
    return render(request, "user.html", {'user':user, "matches_with_ids":matches_with_ids, 'winrate':winrate, 'friend':friend, 'invite':invite})


def friends_view(request, id):
    user = User.objects.all().filter(id=id).first()
    if not user:
        return render(request, "user_doesnt_exist.html")
    friendships = Friendship.objects.filter(Q(person1=user) | Q(person2=user)).order_by('-id')
    only_friends = []
    for friendship in friendships:
        if friendship.person1 == user:
            only_friends.append(friendship.person2)
        else:
            only_friends.append(friendship.person1)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/users.html', {'friends':only_friends})
    return render(request, "users.html", {'friends':only_friends})

def modify_data_for_view():
    output = []
    all_tournaments = get_tournament()
    
    for tournament in all_tournaments:
        userId = tournament[0]
        try:
            user = User.objects.get(id=userId)
            serializer = UserSerializer(user)
            user = serializer.data

        except User.DoesNotExist:
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



@require_POST
def delete_friend(request, user_id):
    print('delte')
    sender = request.user
    other =  User.objects.filter(id=user_id).first()
    if other is None:
        return JsonResponse({'message': 'Not deleted'})
    Friendship.objects.filter(Q(person1=sender, person2=other) | Q(person1=other, person2=sender)).delete()
    return JsonResponse({'message': 'Deleted'})

@require_POST
def add_friend(request, user_id):
    sender = request.user
    send_to = User.objects.filter(id=user_id).first()
    if send_to is not None:
        Invite.objects.filter(sender=sender, send_to=send_to, invite_type=1).delete()
        Invite.objects.create(
            sender=sender,
            send_to=send_to,
            invite_type=1
        )
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'invite',
        {
            'type': 'invite_message',
        }
    )
    return JsonResponse({'message': 'Friend request sent'})

@require_POST
def accept_friend(request, user_id):
    sender = request.user
    send_to = User.objects.filter(id=user_id).first()
    if send_to is not None:
        Invite.objects.filter(sender=send_to, send_to=sender, invite_type=1).delete()
        Friendship.objects.create(person1=sender, person2=send_to)
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'invite',
        {
            'type': 'invite_message',
        }
    )
    return JsonResponse({'message': 'Friend request sent'})

@require_POST
def cancel_friend(request, user_id):
    sender = request.user
    send_to = User.objects.filter(id=user_id).first()
    if send_to is not None:
        Invite.objects.filter(sender=sender, send_to=send_to, invite_type=1).delete()
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'invite',
        {
            'type': 'invite_message',
        }
    )
    return JsonResponse({'message': 'Friend request sent'})

@require_POST
def add_invite(request, user_id):
    sender = request.user
    send_to = User.objects.filter(id=user_id).first()
    if send_to is not None:
        Invite.objects.filter(sender=sender, send_to=send_to, invite_type=2).delete()
        Invite.objects.create(
            sender=sender,
            send_to=send_to,
            invite_type=2
        )
        print('aa')
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'invite',
        {
            'type': 'invite_message',
        }
    )
    return JsonResponse({'message': 'Friend request sent'})

@require_POST
def accept_invite(request, user_id):
    sender = request.user
    send_to = User.objects.filter(id=user_id).first()
    if send_to is not None:
        print(send_to.is_playing, send_to.is_playing)
        if sender.is_playing == False and send_to.is_playing == False:
            print('sending')
            Invite.objects.filter(sender=send_to, send_to=sender, invite_type=2).delete()
            game = GameSession.objects.create(
                player1=sender,
                player2=send_to,
            )
            game.init_game_state()
            channel_layer = get_channel_layer()
            link = f'/game/{game.id}/'
            async_to_sync(channel_layer.group_send)(
                'invite',
                {
                    'type': 'invite_accept',
                    'id1': sender.id,
                    'id2': send_to.id,
                    'link': link
                }
            )
            async_to_sync(channel_layer.group_send)(
                'invite',
                {
                    'type':'invite_message',
                    'id1':sender.id,
                    'id2':send_to.id,
                    'update':0,
                }
            )
    

    return JsonResponse({'message': 'Friend request sent'})


class EmptyPath(GenericAPIView):

	def get(self, request):
		if request.user.is_authenticated:
			print("Empty path, user authenticated")
			return render(request, "partials/home.html")
		print("Empty path, user not authenticated")
		return render(request, "login.html")



def handle_404_view(request, exception):
    return render(request, '404.html', status=404)

def handle_500_view(request):
    return render(request, '500.html', status=500)