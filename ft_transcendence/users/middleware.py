# middleware.py
from django.http import JsonResponse, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib.auth import logout
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timezone
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status

class CookieToAuthorizationMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest' and request.method == 'GET':
            context = {
                'method': 'GET'
            }
            return render(request, 'base.html', context)
        try:
            access_token = request.COOKIES.get('access_token', '')
            if access_token and access_token != '':
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        except:
            pass
