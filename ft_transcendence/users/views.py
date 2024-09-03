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
#	 logout(request)
#	 if request.method == 'POST':
#		 form = AuthenticationForm(data=request.POST)
#		 if form.is_valid():
#			 username = form.cleaned_data.get('username')
#			 password = form.cleaned_data.get('password')
#			 user = authenticate(username=username, password=password)
#			 if user is not None:
#				 login(request, user)
#				 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#			         return JsonResponse({'success': True, 'redirect': 'home'})  # Response for AJAX requests
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

	def post(self, request):
		serializer=self.serializer_class(data=request.data)
		try:
			email=request.data.get('email')
			if email != '' and User.objects.filter(email=email).exists():
				if not User.objects.get(email=email).is_account_active:
					send_code_to_user(email)
					return Response({
						'message': f'Hi Thanks for signing up. A new Passcode hass been sent to your email'
					}, status=status.HTTP_201_CREATED)
				return Response({
						'message': f'user with this Email Address already exists.'
					}, status=status.HTTP_400_BAD_REQUEST)
		except:
			pass

		try:
			if serializer.is_valid(raise_exception=True):
				serializer.save()
				user=serializer.data
				send_code_to_user(user['email'])
				return Response({
					'message': f'hi thanks for signing up. Passcode has been sent to your email'
				}, status=status.HTTP_201_CREATED)
			return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

	def get(self, request):
		return render(request, "register.html")

class VerifyUserEmail(GenericAPIView):
	serializer_class=TrashSerializer
	def post(self, request):
		otpcode=request.data.get('otp')
		email=request.data.get('email')
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
				Please try aga	in'}, status=status.HTTP_401_UNAUTHORIZED)

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
			'message': f'Hi thanks for signing up. Passcode has been sent again to your email'
		}, status=status.HTTP_201_CREATED)





class LoginUserView(GenericAPIView):
	serializer_class = LoginSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data, context={'request': request})
		if serializer.is_valid():
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
		print("---")
		print("---")
		print("---")
		print(request.COOKIES)
		print("---")
		print("---")
		print("---")
		refresh_token = request.COOKIES.get('refresh_token')
		if refresh_token is None:
			return Response({
				'detail': 'Refresh token not provided'
				}, status=status.HTTP_401_UNAUTHORIZED)

		try:
			refresh = RefreshToken(refresh_token)
			new_access_token = str(refresh.access_token)
			response = Response({}, status=status.HTTP_200_OK)
			response.set_cookie('access_token', new_access_token, httponly=True, secure=True, samesite='Strict', max_age=20 * 60)
			return response
		except Exception as e:
			return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)




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





class LogoutUserView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		# print("he IS authenticated!")
		refresh_token = request.COOKIES.get('refresh_token', '')
		# print()
		# print(refresh_token)
		# print()
		# print()
		# print()
		# print()
		# print()
		# print(request.COOKIES)
		# print()
		# print()
		# print()
		# print()
		if not refresh_token:
			return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			# refresh = RefreshToken(refresh_token)  # Decode the token
			response = render(request, "login.html", status=200)
			response.set_cookie('cde', '456', httponly=True, secure=True, samesite='Strict', max_age=20 * 60, path='/')
			response.delete_cookie('refresh_token')
			response.delete_cookie('access_token')
			# user_id = refresh['user_id'] 
			# user = User.objects.get(id=user_id)
			# refresh.access_token.token_blacklist()
			# refresh.token_blacklist()
			return response

		except Exception as e:
			print(e)
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)