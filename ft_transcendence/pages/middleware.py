from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timezone
from django.shortcuts import render

class CheckUserAuthorizationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest' and request.method == 'GET':
            context = {
                'method': 'GET'
            }
            return render(request, 'base.html', context)
        if not request.user.is_authenticated:
            if request.path not in ['/login/', '/register/', '/inactive/', '/admin/']:
                return redirect('/login/')
        elif not request.user.is_account_active:
            logout(request)
            return redirect('/inactive/')