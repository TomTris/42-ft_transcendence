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
from rest_framework_simplejwt.tokens import RefreshToken,  Token
from rest_framework_simplejwt.authentication import JWTAuthentication

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        return super().authenticate(request)

def valid_access_token(request):
    access_token = request.COOKIES.get('access_token', '')
    if access_token:
        jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        checker = CustomJWTAuthentication()
        checker.authenticate(request)
    else:
        raise Exception("")
    

class CookieToAuthorizationMiddleware(MiddlewareMixin):
    non_login = ['/login/', '/login', '/register', '/register/',\
                 '/inactive/', '/admin/',
                 '/password_reset-request/']

    def process_request(self, request):
        print()
        print(request.path, "with", request.method, "Method")
        if request.method == 'GET':
            if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                context = {
                    'method': 'GET'
                }
                print("New Request")
                return render(request, 'base.html', context, status=status.HTTP_307_TEMPORARY_REDIRECT)
            
            try:
                valid_access_token(request)
                print("HTTP_AUTHORIZATION GET set")
                if request.path in self.non_login:
                    print("redirect to home.html")
                    return render(request, "home.html")
                print("redirect to", request.path)
            except:
                print("HTTP_AUTHORIZATION POST unset")
                request.META.pop('HTTP_AUTHORIZATION', None)
                if request.path not in self.non_login and not request.path.startswith('/password-reset-confirm/'):
                    return render(request, "login.html")
            
        if request.method == 'POST':
            try:
                valid_access_token(request)
                print("HTTP_AUTHORIZATION POST set")
            except:
                pass
                request.META.pop('HTTP_AUTHORIZATION', None)
                print("HTTP_AUTHORIZATION POST not set")
