from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timezone
from django.shortcuts import render
# from django.shortcuts import render, redirect
# from .admin import UserCreationForm
# from django.contrib.auth import authenticate, login, logout
# from django.shortcuts import render, redirect
# from django.contrib.auth.forms import AuthenticationForm
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse

# @csrf_exempt
# def login_view(request):
#     logout(request)
#     if request.method == 'POST':
#         form = AuthenticationForm(data=request.POST)
#         if form.is_valid():
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password')
#             user = authenticate(username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                     return JsonResponse({'success': True, 'redirect': 'home'})  # Response for AJAX requests
#                 else:
#                     return redirect('home')  # Response for normal form submissions
#             else:
#                 # Invalid credentials
#                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                     return JsonResponse({'success': False, 'error': 'Invalid username or password'}, status=400)
#                 else:
#                     form.add_error(None, 'Invalid username or password')
#         else:
#             # Form is not valid
#             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                 return JsonResponse({'success': False, 'error': 'Form is not valid'}, status=400)
#             else:
#                 form.add_error(None, 'Form is not valid')
#     else:
#         form = AuthenticationForm()

#     # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#     #     return render(request, 'partials/login.html', {'form': form})  # Partial template for AJAX requests
#     return render(request, 'login.html', {'form': form})

# @csrf_exempt
# def register_view(request):
#     logout(request)
#     if request.method == "POST":
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect("login")
#     else:
#         form = UserCreationForm()
#     return render(request, "register.html", {"form":form})
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect
from rest_framework.views import APIView
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
		print(request)
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
			response = Response({
				'access_token': serializer.validated_data['access_token'],
				'refresh_token': serializer.validated_data['refresh_token'],
				'redirect_url': reverse('home')
			}, status=status.HTTP_200_OK)
			response.set_cookie('access_token', serializer.validated_data['access_token'], httponly=True, secure=True, samesite='Strict', max_age=15 * 60, path='/')
			response.set_cookie('refresh_token', serializer.validated_data['refresh_token'], httponly=True, secure=True, samesite='Strict', max_age=7 * 24 * 60 * 60, path='/accounts/refresh')
			return response
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def get(self, request):
		return render(request, "login-verify.html")





class TokenRefreshView(APIView):
	def get(self, request):
		refresh_token = request.COOKIES.get('refresh_token')
		if refresh_token is None:
			return Response({
				'detail': 'Refresh token not provided',
				'redirect_url': reverse('login')
				}, status=status.HTTP_401_UNAUTHORIZED)

		try:
			refresh = RefreshToken(refresh_token)
			new_access_token = str(refresh.access_token)
			response = Response({'access_token': new_access_token}, status=status.HTTP_200_OK)
			response.set_cookie('access_token', new_access_token, httponly=True, secure=True, samesite='Strict', max_age=15 * 60)
			return response
		except Exception as e:
			return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)




class HomeView(GenericAPIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		return render(request, "home.html")

class EmptyPath(GenericAPIView):

	def get(self, request):
		if request.user.is_authenticated:
			return render(request, "home.html")
		return render(request, "login.html")



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
	serializer_class=TrashSerializer
	def get(self, request, uidb64, token):
		try:
			user_id=smart_str(urlsafe_base64_decode(uidb64))
			user=User.objects.get(id=user_id)
			user_row = OneTimePasswordReset.objects.get(user=user)
			if user_row.reset_token != token or user_row.times != 0:
				return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)
			user_row.reset_token=PasswordResetTokenGenerator().make_token(user)
			user_row.times = 1
			user_row.save()
			return Response({
				'success': True,
				'message': 'Credentials are valid',
				'uidb64': uidb64,
				'token': user_row.reset_token
				# 'redirect_url': reverse('password_reset-set_new')
				}, status=status.HTTP_200_OK)
		except User.DoesNotExist:
			return Response({'message':'User not found'}, status=status.HTTP_400_BAD_REQUEST)
		except OneTimePasswordReset.DoesNotExist:
			return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)
		except DjangoUnicodeDecodeError:
			return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)

class SetNewPassword(GenericAPIView):
	serializer_class=SetNewPasswordSerializer
	def post(self, request):
		serializer=self.serializer_class(data=request.data)
		serializer.is_valid(raise_exception=True)
		return Response({
			'message':'passwort reset successfull',
			# 'redirect_url': reverse('login')
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

