from django.shortcuts import render, redirect
from rest_framework.generics import GenericAPIView
from .serializers import (UserRegisterSerializer, LoginSerializer, PasswordResetRequestSerializer,
						  SetNewPasswordSerializer, LogoutUserSeriallizer, TrashSerializer, VerifyLoginSerializer)
from django.urls import reverse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .utils import send_code_to_user, send_code_to_user_login, send_normal_email
from .models import OneTimePassword, OneTimePasswordLogin, User, OneTimePasswordReset
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
# Create your views here.

class RegisterUserView(GenericAPIView):
	serializer_class=UserRegisterSerializer

	def post(self, request):
		serializer=self.serializer_class(data=request.data)
		if serializer.is_valid(raise_exception=True):
			serializer.save()
			user=serializer.data
			send_code_to_user(user['email'])
			return Response({
				'data':user,
				'message': f'hi thanks for signing up. Passcode has been sent to your email',
				'redirect_url': reverse('register-verify')
			}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def get(self, request):
		return render(request, "register.html")


class VerifyUserEmail(GenericAPIView):
	serializer_class=TrashSerializer
	def post(self, request):
		otpcode=request.data.get('otp')
		email=request.data.get('email')
		print(OneTimePassword.objects)
		if email is None or otpcode is None:
			return Response({'message':'code or email is invalid'}, status=status.HTTP_400_BAD_REQUEST)
		try:
			user_row = OneTimePassword.objects.get(email=email)
		except OneTimePassword.DoesNotExist as e:
			return Response({'message':'code or email is invalid'}, status=status.HTTP_400_BAD_REQUEST)
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
					'message': 'account email verified successfully',
					'redirect_url': reverse('login')}, status=status.HTTP_200_OK)
		if user_row.times == 2:
			OneTimePassword.delete_for_user(user=user_row.user)
			return Response({
				'message':'code is invalid. You tried already 3 times.\n\
					Please get the new Code for verifying and try again',
				'redirect_url': reverse('register-send_OTP')},
				status=status.HTTP_400_BAD_REQUEST)
		user_row.times += 1
		user_row.save()
		return Response({'message':'code or email is invalid.\n\
				Please try again'}, status=status.HTTP_400_BAD_REQUEST)

	def get(self, request):
		return render(request, "register-verify.html")

# havent checked
class SendRegisterCode(GenericAPIView):
	serializer_class=TrashSerializer
	def post(self, request):
		email=request.data.get('email', default='')
		user=User.objects.get(email=email, default=None)
		if user is None or user.is_verified == True:
			return Response({'message':'email is invalid'}, status=status.HTTP_400_BAD_REQUEST)
		send_code_to_user(email)
		return Response({
			'data':user,
			'message': f'Hi thanks for signing up. Passcode has been sent again to your email',
			'redirect_url': reverse('register-verify')
		}, status=status.HTTP_201_CREATED)





class LoginUserView(GenericAPIView):
	serializer_class = LoginSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data, context={'request': request})
		if serializer.is_valid():
			send_code_to_user_login(serializer.validated_data)
			return Response({
				'message':"Please open your mail to get OTP to login",
				'redirect_url': reverse('login-verify')}, status=status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def get(self, request):
		return render(request, "login.html")

class VerifyLoginUserView(GenericAPIView):
	serializer_class = VerifyLoginSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data, context={'request': request})
		if serializer.is_valid():
			return Response(serializer.validated_data, status=status.HTTP_200_OK)
		print(1111)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def get(self, request):
		return render(request, "login-verify.html")





class TestAuthenticationView(GenericAPIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		# return render(request, "login_ok.html")
		data={
			'msg': 'it works'
		}
		# redirect("/home.html/")
		return Response(data, status=status.HTTP_200_OK)




class PasswordResetRequestView(GenericAPIView):
	serializer_class=PasswordResetRequestSerializer
	def post(self, request):
		serializer=self.serializer_class(data=request.data, context={'request':request})
		serializer.is_valid(raise_exception=True)
		return Response({
			'message':"A verify-link has been sent to your email to reset your password",
			}, status=status.HTTP_200_OK)
	
	def get(self, request):
		return render(request, 'password_reset-request.html')

class PasswordResetConfirm(GenericAPIView):
	serializer_class=PasswordResetRequestSerializer
	def get(self, request, uidb64, token):
		try:
			user_id=smart_str(urlsafe_base64_decode(uidb64))
			try:
				user=User.objects.get(id=user_id)
			except User.DoesNotExist:
				return Response({'message':'User not found'}, status=status.HTTP_400_BAD_REQUEST)
			if user == None:
				return Response({'message':'Email doesn\'t exists'}, status=status.HTTP_400_BAD_REQUEST)
			try:
				user_row = OneTimePasswordReset.objects.get(user=user)
			except:
				return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)
			if user_row == None:
				return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)
			if user_row.times == 1:
				return Response({'message':'token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
			user_row.times = 1
			return Response({
				'success': True,
				'message': 'Credentials are valid',
				'uidb64': uidb64,
				'token': token,
				'redirect_url': reverse('password_reset-set_new')}, status=status.HTTP_200_OK)
		except DjangoUnicodeDecodeError:
			return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)

class SetNewPassword(GenericAPIView):
	serializer_class=SetNewPasswordSerializer
	def post(self, request):
		serializer=self.serializer_class(data=request.data)
		serializer.is_valid(raise_exception=True)
		return Response({
			'message':'passwort reset successfull',
			'redirect_url': reverse('login')
			}, status=status.HTTP_200_OK)
	
	def get(self, request):
		return render(request, 'password_reset-set_new.html')




class LogoutUserView(GenericAPIView):
	serializer_class=LogoutUserSeriallizer
	permission_classes=[IsAuthenticated]

	def post(self, request):
		serializer=self.serializer_class(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(status=status.HTTP_204_NO_CONTENT)
	
class HomeView(GenericAPIView):
	def get(self, request):
		return render(request, "home.html")