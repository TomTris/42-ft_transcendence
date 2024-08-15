from django.shortcuts import render, redirect
from users.models import MyUser

def home_view(request):
    return render(request, "home.html")

def inactive_view(request):
    return render(request, "inactive.html")

def best_view(request):
    return render(request, "index.html")

def users_view(request):
    users = MyUser.objects.all()
    return render(request, "users.html", {'users':users, 'amount':len(users)})

def user_view(request, id):
    user = MyUser.objects.all()
    if id >= len(user):
        return render(request, "user_doesnt_exist.html")
    user = user[id]
    return render(request, "user.html", {'user':user})