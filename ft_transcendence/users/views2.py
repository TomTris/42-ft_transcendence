import os
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timezone
from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken, BlacklistedToken
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from .serializers import (UserRegisterSerializer, LoginSerializer, PasswordResetRequestSerializer,
						  SetNewPasswordSerializer, TrashSerializer, VerifyLoginSerializer)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .utils import send_code_to_user, send_code_to_user_login, send_normal_email
from .models import OneTimePassword, OneTimePasswordLogin, User, OneTimePasswordReset
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.authentication import JWTAuthentication
from .forms import UserSettingsForm 

class LogoutUserView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		refresh_token = request.COOKIES.get('refresh_token', '')
		
		if not refresh_token:
			return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			response = render(request, "login.html", status=200)
			response.delete_cookie('refresh_token', samesite='Strict', path='/refresh/')
			response.delete_cookie('access_token', samesite='Strict', path='/')
			old_refresh = RefreshToken(token=refresh_token)
			old_refresh.blacklist()	
			return response

		except Exception as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class IsAuthorizedView(APIView):
	def post(self, request):
		if request.user.is_authenticated:
			return Response({}, status=status.HTTP_200_OK)
		return Response({}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class NavbarAuthorizedView(APIView):

	def post(self, request):
		if request.user.is_authenticated:
			return render(request, "navbar_authorized.html", status=200)
		return render(request, "navbar_unauthorized.html", status=200)

class TokenRefreshView(APIView):
	def post(self, request):
		refresh_token = request.COOKIES.get('refresh_token')
		if refresh_token is None:
			return Response({
				'detail': 'Refresh token not provided'
				}, status=status.HTTP_204_NO_CONTENT)

		try:
			refresh = RefreshToken(refresh_token)
			new_access_token = str(refresh.access_token)
			response = Response({}, status=status.HTTP_200_OK)
			response.set_cookie('access_token', new_access_token, httponly=True, secure=True, samesite='Strict', max_age=20 * 60, path='/')
			return response
		except Exception as e:
			return Response({'detail': str(e)}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)


class SettingView(APIView):
	permission_classes = [IsAuthenticated]
	def get(self, request):
		try:
			user = request.user
			context = {
				'email': user.email,
				'first_name': user.first_name,
				'last_name': user.last_name,
				'username': user.username,
				'is_verified': user.is_verified,
				'date_joined': user.date_joined,
				'twoFaEnable': user.twoFaEnable,
				'is_subscribe': user.is_subscribe,
				'avatar': user.avatar,
				}
			return render(request, "settings.html", context, status=200)
		except Exception as e:
			return Response({'detail': str(e)}, status=status.HTTP_204_NO_CONTENT)
	
	def post(self, request):
		user = request.user
		try:
			form = UserSettingsForm(request.POST, request.FILES, instance=user)
			old_avatar_url = user.avatar.url
			if form.is_valid():
				form.save()
				if old_avatar_url != user.avatar.url and old_avatar_url != '/media/default/default.png':
					old_avatar_url = os.getcwd() + old_avatar_url
					os.remove(old_avatar_url)
			
				return Response({'message': 'Profile updated successfully!'}, status=status.HTTP_200_OK)
			else:
				return Response({'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)