# middleware.py

from django.utils.deprecation import MiddlewareMixin

class CookieToAuthorizationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            access_token = request.COOKIES.get('access_token', '')
        except:
            pass
        if access_token and access_token != '':
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

