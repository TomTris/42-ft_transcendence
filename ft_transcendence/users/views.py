from django.contrib.auth import authenticate, login
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



class RegisterUserView(GenericAPIView):
	serializer_class=UserRegisterSerializer

	def response_message(self, is_registered, account_active):
		if account_active == 1:
			msg = 'user with this Email Address already exists and is actived.'
			return Response({"message" : msg}, status=status.HTTP_400_BAD_REQUEST)
		if is_registered == 1:
			msg = 'This account is already registered, but not verified. New code has been sent to your email. Please check and verify.'
			return Response({"message" : msg}, status=status.HTTP_200_OK)
		if is_registered == 2:
			msg = 'Username has been used.'
			return Response({"message" : msg}, status=status.HTTP_400_BAD_REQUEST)
		msg = 'Thanks for signing up. New Passcode has been sent to your mail'
		return Response({"message" : msg}, status=status.HTTP_201_CREATED)

	def post(self, request):
		serializer=self.serializer_class(data=request.data)
		is_registered = 0
		account_active = 0
		try:
			email=request.data.get('email', '')
			if email and User.objects.filter(email=email).exists():
				is_registered = 1
				if User.objects.filter(email=email).first().is_verified:
					account_active = 1
			if account_active == 1:
				return self.response_message(is_registered,account_active)
			if is_registered == 1:
				send_code_to_user(request.data['email'])
				return self.response_message(is_registered,account_active)
			if request.data['username']:
				if User.objects.filter(username=request.data['username']).exists():
					return self.response_message(2, 0)
			if serializer.is_valid(raise_exception=True):
				serializer.save()
				send_code_to_user(request.data['email'])
				return self.response_message(is_registered,account_active)
			
			return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

	def get(self, request):
		return render(request, "register.html")

class VerifyUserEmail(GenericAPIView):
	serializer_class=TrashSerializer
	def post(self, request):
		try:
			otpcode=request.data.get('otp')
			email=request.data.get('email')
		except:
			return Response({'message':'code or email is invalid.\n\
				Please try again'}, status=status.HTTP_401_UNAUTHORIZED)
		if email is None or otpcode is None:
			return Response({'message':'code or email is invalid'}, status=status.HTTP_401_UNAUTHORIZED)
		try:
			user_row = OneTimePassword.objects.get(email=email)
		except OneTimePassword.DoesNotExist as e:
			return Response({'message':'code or email is invalid'}, status=status.HTTP_401_UNAUTHORIZED)
		if user_row.code == otpcode:
				user_row.user.is_verified = True
				user_row.user.save()
				OneTimePassword.delete_for_user(user=user_row.user)
				data={
					'email_body':"Your Email was actived successfully",
					'email_subject':"Account Activation",
					'to_email':email
				}
				send_normal_email(data)
				return Response({
					'message': f'hi thanks for signing up. Passcode has been sent to your email',
				}, status=status.HTTP_201_CREATED)
		if user_row.times == 2:
			OneTimePassword.delete_for_user(user=user_row.user)
			return Response({
				'message':'code is invalid. You tried already 3 times.\n\
					Please get the new Code for verifying and try again'
					}, status=status.HTTP_401_UNAUTHORIZED)
		user_row.times += 1
		user_row.save()
		return Response({'message':'code or email is invalid.\n\
				Please try again'}, status=status.HTTP_401_UNAUTHORIZED)

	def get(self, request):
		return render(request, "register-verify.html")

class SendRegisterCode(GenericAPIView):
	serializer_class=TrashSerializer
	def post(self, request):
		try:
			email=request.data.get('email')
			user=User.objects.get(email=email)
		except:
			return Response({'message':'email is invalid.\n\
				Please try again'}, status=status.HTTP_401_UNAUTHORIZED)
		if user is None or user.is_verified == True:
			return Response({'message':'email is invalid'}, status=status.HTTP_400_BAD_REQUEST)
		send_code_to_user(email)
		return Response({
			'message': f'Hi thanks for signing up. Passcode has been sent again to your email'
		}, status=status.HTTP_201_CREATED)



class LoginUserView(GenericAPIView):
	serializer_class = LoginSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data, context={'request': request})
		if serializer.is_valid():
			user = User.objects.get(email=serializer.validated_data)
			if user.twoFaEnable == False:
				data={
				'email_body':"You have just loggined",
				'email_subject':"Your Login",
				'to_email':serializer.validated_data
				}
				send_normal_email(data)
				user_tokens=user.tokens()
				response = Response({
				"message" : "Login successful"
					}, status=status.HTTP_202_ACCEPTED)
				response.set_cookie('access_token', str(user_tokens.get('access')), httponly=True, secure=True, samesite='Strict', max_age=20 * 60, path='/')
				response.set_cookie('refresh_token', str(user_tokens.get('refresh')), httponly=True, secure=True, samesite='Strict', max_age=24*60*60, path='/refresh/')
				login(request, user)
				return response
			send_code_to_user_login(serializer.validated_data)
			return Response({
				'message':"Please open your mail to get OTP to login"
				}, status=status.HTTP_200_OK)
		return Response({
			"message": f"Login or Password is wrong"
				}, status=status.HTTP_401_UNAUTHORIZED)

	def get(self, request):
		return render(request, "login.html")

class VerifyLoginUserView(GenericAPIView):
	serializer_class = VerifyLoginSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data, context={'request': request})
		if serializer.is_valid():
			response = Response({
				"message" : "Login successful"
			}, status=status.HTTP_200_OK)
			response.set_cookie('access_token', serializer.validated_data['access_token'], httponly=True, secure=True, samesite='Strict', max_age=20 * 60, path='/')
			response.set_cookie('refresh_token', serializer.validated_data['refresh_token'], httponly=True, secure=True, samesite='Strict', max_age=24*60*60, path='/refresh/')
			return response
		return Response({"message": "code or email is invalid"}, status=status.HTTP_401_UNAUTHORIZED)	

	def get(self, request):
		return render(request, "login-verify.html")




class PasswordResetRequestView(GenericAPIView):
	serializer_class=PasswordResetRequestSerializer
	def post(self, request):
		serializer=self.serializer_class(data=request.data, context={'request':request})
		try:
			if serializer.is_valid():
				return Response({
					'message':"A verify-link has been sent to your email to reset your password",
					}, status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				'error': str(e),
				}, status=status.HTTP_200_OK)
		return Response({
				'error': str(serializer.errors),
				}, status=status.HTTP_200_OK)
	
	def get(self, request):
		return render(request, 'password_reset-request.html')


class PasswordResetConfirm(GenericAPIView):
	serializer_class=TrashSerializer
	def get(self, request, uidb64, token):
		try:
			user_id=smart_str(urlsafe_base64_decode(uidb64))
			user=User.objects.get(id=user_id)
			user_row = OneTimePasswordReset.objects.get(user=user)
			if user_row.reset_token != token or user_row.times != 0:
				return Response({'message':'token is invalid or has expired'}, status=status.HTTP_400_BAD_REQUEST)
			user_row.reset_token=PasswordResetTokenGenerator().make_token(user)
			user_row.times = 1
			user_row.save()
			context = {
				'uidb64': uidb64,
				'token': user_row.reset_token
				}
			return render(request, "password_reset-set_new.html", context, status=200)
		except User.DoesNotExist:
			return render (request, "login.html", {'message':'User not found'}, status=status.HTTP_400_BAD_REQUEST)
		except OneTimePasswordReset.DoesNotExist:
			return render (request, "login.html", {'message':'token is invalid or has expired'}, status=status.HTTP_400_BAD_REQUEST)
		except DjangoUnicodeDecodeError:
			return render (request, "login.html", {'message':'token is invalid or has expired'}, status=status.HTTP_400_BAD_REQUEST)


class SetNewPassword(GenericAPIView):
	serializer_class=SetNewPasswordSerializer
	def post(self, request):
		serializer=self.serializer_class(data=request.data)
		serializer.is_valid(raise_exception=True)
		return Response({
			'message':'passwort reset successfull',
			}, status=status.HTTP_200_OK)

