# middleware.py
from django.http import JsonResponse, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timezone
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
import jwt
from django.conf import settings
from .models import User
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import get_authorization_header
from rest_framework import status

def valid_access_token(access_token):
    try:
        if access_token and access_token != '':
            jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
            return True
        return False
    except:
        return False
    

class CookieToAuthorizationMiddleware(MiddlewareMixin):
    non_login = ['/login/', '/login', '/register', '/register/',\
                 '/inactive/', '/admin/',
                 '/password_reset-request/']

    def process_request(self, request):
        if request.method == 'GET':
            if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                context = {
                    'method': 'GET'
                }
                return render(request, 'base.html', context, status=status.HTTP_307_TEMPORARY_REDIRECT)
            print()
            print("process_request GET partial")
            access_token = request.COOKIES.get('access_token', '')
            if valid_access_token(access_token):
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
                print("HTTP_AUTHORIZATION set")
                if request.path in self.non_login:
                    print("redirect to home")
                    return render(request, "home.html")
            else:
                print("HTTP_AUTHORIZATION not set")
                if request.path not in self.non_login and not request.path.startswith('/password-reset-confirm/'):
                    print("redirect to login")
                    return render(request, "login.html")
        if request.method == 'POST':
            access_token = request.COOKIES.get('access_token', '')
            print("HTTP_AUTHORIZATION POST set")
            if valid_access_token(access_token):
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
            else:
                print("HTTP_AUTHORIZATION POST not set")