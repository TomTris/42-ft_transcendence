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
from chat.models import BlockList
from .serializers import BlockListSerializer
import json
from django.http import JsonResponse
from .serializers import InviteSerializer, UserSerializer

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


def best_view(request):
    return render(request, "index.html")

def users_view(request):
    users = User.objects.order_by("id")
    # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return render(request, 'partials/users.html', {'friends':users})
    # return render(request, "users.html", {'friends':users})

def user_view(request, id):
    curent_user = request.user
    user = User.objects.all().filter(id=id).first()
    if not user:
        return render(request, "user_doesnt_exist.html")
    
    matches = GameSession.objects.filter(Q(player1=user) | Q(player2=user)).order_by('-id')
    matches_with_ids = []
    for match in matches:
        if match.player1 == user:
            match_data = {
                'match': match,
                'enemy': match.player2,
                'score_user': match.score1,
                'score_enemy': match.score2,
                'rank_change':match.rank_change1,
                'type':"Matchmaking" if match.is_tournament == False else "Tournament"
            }
        else:
            match_data = {
                'match': match,
                'enemy': match.player1,
                'score_user': match.score2,
                'score_enemy': match.score1,
                'rank_change':match.rank_change1,
                'type':"Matchmaking" if match.is_tournament == False else "Tournament"
            }
            
        matches_with_ids.append(match_data)
    if user.total == 0:
        winrate = 0
    else:
        winrate = "%.2f" % (user.wins / user.total * 100.0)

    friend=get_friend_status(curent_user, user)
    invite = get_invite_status(curent_user, user)

    # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return render(request, 'partials/user.html', {'user':user, "matches_with_ids":matches_with_ids, 'winrate':winrate, 'friend':friend, 'invite':invite})
    # return render(request, "user.html", {'user':user, "matches_with_ids":matches_with_ids, 'winrate':winrate, 'friend':friend, 'invite':invite})


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
    # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return render(request, 'partials/users.html', {'friends':only_friends})
    # return render(request, "users.html", {'friends':only_friends})


def get_pos1(tournament):
    scores = tournament[4]
    users = tournament[5]
    if scores[0] == 0 and scores[1] == 0:
        if scores[2] > scores[3]:
            return users[2]
        else:
            return users[3]
    elif scores[2] == 0 and scores[3] == 0:
        if scores[0] > scores[1]:
            return users[0]
        else:
            return users[1]
    else:
        if scores[0] > scores[1]:
            f1 = 0
        else:
            f1 = 1
        if scores[2] > scores[3]:
            f2 = 2
        else:
            f2 = 3
        if scores[4] > scores[5]:
            return users[f1]
        else:
            return users[f2]
        
def get_pos2(tournament):
    scores = tournament[4]
    users = tournament[5]
    if scores[0] == 0 and scores[1] == 0:
        if scores[2] < scores[3]:
            return users[2]
        else:
            return users[3]
    elif scores[2] == 0 and scores[3] == 0:
        if scores[0] < scores[1]:
            return users[0]
        else:
            return users[1]
    else:
        if scores[0] > scores[1]:
            f1 = 0
        else:
            f1 = 1
        if scores[2] > scores[3]:
            f2 = 2
        else:
            f2 = 3
        if scores[4] < scores[5]:
            return users[f1]
        else:
            return users[f2]
        
def get_pos3_1(tournament):
    scores = tournament[4]
    users = tournament[5]
    if scores[0] == 0 and scores[1] == 0:
        return users[0]
    elif scores[2] == 0 and scores[3] == 0:
        return users[2]
    else:
        if scores[0] > scores[1]:
            return users[1]
        else:
            return users[0]
        
def get_pos3_2(tournament):
    scores = tournament[4]
    users = tournament[5]
    if scores[0] == 0 and scores[1] == 0:
        return users[1]
    elif scores[2] == 0 and scores[3] == 0:
        return users[3]
    else:
        if scores[2] > scores[3]:
            return users[3]
        else:
            return users[2]


def modify_data_for_view():
    output = []
    all_tournaments = get_tournament()
    
    for tournament in all_tournaments:
        userId = tournament[0]
        try:
            user = User.objects.get(username=userId)
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
            'online':tournament[2],
            'pos1': get_pos1(tournament),
            'pos2': get_pos2(tournament),
            'pos3_1': get_pos3_1(tournament),
            'pos3_2': get_pos3_2(tournament),
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
    # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return render(request, 'partials/tournaments.html', data)
    # return render(request, "tournaments.html", data)


def block_list_view(request):
    user = request.user
    blocked = BlockList.objects.filter(blocker=user)
    serialized = BlockListSerializer(blocked, many=True)
    # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return render(request, 'partials/block_list.html', {'blocked':serialized.data}) 

def unblock(request):
    data = json.loads(request.body)
    id = data['block_id']
    BlockList.objects.filter(id=id).delete()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'chat',
        {
            'type': 'sending_to_one',
            'id':request.user.id
        }
    )
    return JsonResponse({'status': 'success', 'message': 'User unblocked successfully', 'ok':True})

def invite_list_view(request):
    user = request.user
    invites = Invite.objects.filter(sender=user).order_by('-id')
    serialized = InviteSerializer(invites, many=True)
    return render(request, 'partials/invite_list.html', {'blocked':serialized.data}) 

def canceling_invite(request):
    data = json.loads(request.body)
    id = data['block_id']
    in1 = Invite.objects.filter(id=id).first()
    id1 = in1.sender.id
    id2 = in1.send_to.id
    in1.delete()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'invite',
        {
            'type': 'invite_message',
            'id1':id1,
            'id2':id2,
            'update':2,
        }
    )
    return JsonResponse({'status': 'success', 'message': 'User unblocked successfully', 'ok':True})


#for test modsecurity
from django.http import HttpResponse
from django.db import connection
def vulnerable_view(request):
    query_param = request.GET.get('id', '')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM users_user")
    results = cursor.fetchall()
    return HttpResponse(f"Results: {results}")



@require_POST
def delete_friend(request, user_id):
    sender = request.user
    other =  User.objects.filter(id=user_id).first()
    if other is None:
        return JsonResponse({'message': 'Not deleted'})
    Friendship.objects.filter(Q(person1=sender, person2=other) | Q(person1=other, person2=sender)).delete()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'invite',
        {
            'type': 'invite_message',
            'id1':sender.id,
            'id2':other.id,
            'update':2,
        }
    )
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
            'id1':sender.id,
            'id2':send_to.id,
            'update':2,
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
            'id1':sender.id,
            'id2':send_to.id,
            'update':2,
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
            'id1':sender.id,
            'id2':send_to.id,
            'update':2,
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
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'invite',
        {
            'type': 'invite_message',
            'id1':sender.id,
            'id2':send_to.id,
            'update':2,
        }
    )
    return JsonResponse({'message': 'Friend request sent'})

@require_POST
def accept_invite(request, user_id):
    sender = request.user
    send_to = User.objects.filter(id=user_id).first()
    if send_to is not None:
        if sender.is_playing == False and send_to.is_playing == False:
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

@require_POST
def play_invite(request, user_id):
    sender = request.user
    send_to = User.objects.filter(id=user_id).first()
    if send_to is not None:
        game = GameSession.objects.filter(Q(player1=sender, player2=send_to) | Q(player1=send_to, player2=sender), is_active=True).first()
        if game:
            channel_layer = get_channel_layer()
            link = f'/game/{game.id}/'
            async_to_sync(channel_layer.group_send)(
                'invite',
                {
                    'type': 'invite_accept',
                    'id1': sender.id,
                    'id2': -1,
                    'link': link
                }
            )
    return JsonResponse({'message': 'Friend request sent'})



@require_POST
def cancel_invite(request, user_id):
    sender = request.user
    send_to = User.objects.filter(id=user_id).first()
    if send_to is not None:
        Invite.objects.filter(sender=sender, send_to=send_to, invite_type=2).delete()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'invite',
            {
                'type': 'invite_message',
                'id1':sender.id,
                'id2':send_to.id,
                'update':2,
            }
        )
    return JsonResponse({'message': 'Friend request sent'})


class EmptyPath(GenericAPIView):

	def get(self, request):
		if request.user.is_authenticated:
			return render(request, "partials/home.html")
		return render(request, "login.html")



def handle_404_view(request, exception):
    return render(request, '404.html', status=404)

def handle_500_view(request):
    return render(request, '500.html', status=500)

class Chat(GenericAPIView):

	def post(self, request):
		if request.user.is_authenticated:
			return render(request, "chat.html")