# middleware.py

from django.utils.deprecation import MiddlewareMixin

class CookieToAuthorizationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Extract the 'access_token' from the cookies
        try:
            access_token = request.COOKIES.get('access_token', '')
        except:
            pass
        print(request.COOKIES)
        print(1111111)
        print(access_token)
        print(1111111)
        # If the access token is present, set the 'Authorization' header
        if access_token and access_token != '':
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
            print(request.META['HTTP_AUTHORIZATION'])
        print(1111111)
        print(1111111)
        print(1111111)
