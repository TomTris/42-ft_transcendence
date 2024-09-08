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
from .models import User

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        return super().authenticate(request)

def valid_access_token(request):
    access_token = request.COOKIES.get('access_token', '')
    if access_token:
        try:
            decoded_data = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
            checker = CustomJWTAuthentication()
            user_id = decoded_data.get('user_id')
            user = User.objects.get(id=user_id)
            checker.authenticate(request)
            request.user = user
        except Exception as e:
            raise Exception("")
    else:
        raise Exception("")
    


class CookieToAuthorizationMiddleware(MiddlewareMixin):
    non_login = ['/login/', '/login', '/register', '/register/',\
                 '/inactive/', '/admin/',
                 '/password_reset-request/']

    def process_request(self, request):
        if request.method == 'GET':
            if request.headers.get('X-Requested-With') != 'XMLHttpRequest' and not request.path.startswith('/media/'):
                context = {
                    'method': 'GET',
                    'Location' : '/'
                }
                return render(request, 'base.html', context, status=status.HTTP_302_FOUND)
            
            try:
                valid_access_token(request)
                
                if request.path in self.non_login:
                    response = render(request, "partials/home.html")
                    return response
            except:
                request.META.pop('HTTP_AUTHORIZATION', None)
                if request.path not in self.non_login and not request.path.startswith('/password-reset-confirm/'):
                    return render(request, "login.html")
            
        if request.method == 'POST':
            try:
                valid_access_token(request)
            except:
                pass
                request.META.pop('HTTP_AUTHORIZATION', None)



# users/middleware.py

import jwt
from channels.auth import AuthMiddleware
from channels.exceptions import DenyConnection
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Process WebSocket requests
        if scope['type'] == 'websocket':
            token = self._get_token_from_cookies(scope)
            user = await self._authenticate(token)
            scope['user'] = user
        
        # Pass control to the next middleware or consumer
        return await self.inner(scope, receive, send)

    def _get_token_from_cookies(self, scope):
        cookies_header = dict(scope.get('headers', []))
        cookie_header = cookies_header.get(b'cookie', b'')
        cookies = cookie_header.decode().split('; ')

        for cookie in cookies:
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                if key == 'access_token':
                    return value
        return None

    @database_sync_to_async
    def _authenticate(self, token):
        if token is None:
            return AnonymousUser()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if user_id:
                return User.objects.get(id=user_id)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            pass
        return AnonymousUser()