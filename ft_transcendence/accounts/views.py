from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from .serializers import UserRegisterSerializer, LoginSerializer, PasswordResetRequestSerializer, SetNewPasswordSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .utils import send_code_to_user
from .models import OneTimePassword, User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
# Create your views here.


class RegisterUserView(GenericAPIView):
	serializer_class=UserRegisterSerializer

	def post(self, request):
		user_data=request.data
		serializer=self.serializer_class(data=user_data)
		if serializer.is_valid(raise_exception=True):
			serializer.save()
			user=serializer.data
			send_code_to_user(user['email'])
			return Response({
				'data':user,
				'message': f'hi thanks for signing up. Passcode has been sent to your email'	
			}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def get(self, request):
		return render(request, "register.html")


class VerifyUserEmail(GenericAPIView):
	serializer_class=LoginSerializer

	def post(self, request):
		try:
			otpcode=request.data.get('otp')
			user_code_obj=OneTimePassword.objects.get(code=otpcode)
			user = user_code_obj.user
			if not user.is_verified:
				user.is_verified = True
				user.save()
				return Response({
					'message': 'account email verified successfully'
				}, status=status.HTTP_200_OK)
			return Response({
				'message':'code is invalid. User is already verified'
			}, status=status.HTTP_204_NO_CONTENT)
		except OneTimePassword.DoesNotExist:
			return Response({'message' : 'passcode not provided'}, status=status.HTTP_404_NOT_FOUND)


class LoginUserView(GenericAPIView):
	serializer_class = LoginSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data, context={'request': request})
		if serializer.is_valid():
			return Response(serializer.validated_data, status=status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	
	def get(self, request):
		return render(request, "login.html")


class TestAuthenticationView(GenericAPIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		# return render(request, "login_ok.html")
		data={
			'msg': 'it works'
		}
		return Response(data, status=status.HTTP_200_OK)


class PasswordResetRequestView(GenericAPIView):
	serializer_class=PasswordResetRequestSerializer
	def post(self, request):
		serializer=self.serializer_class(data=request.data, context={'request':request})
		serializer.is_valid(raise_exception=True)
		return Response({'message':"a link has been sent to your email to reset your password"}, status=status.HTTP_200_OK)


# Better idea: if want to reset -> type email, send back token. Then verify by using email, new password and token a gain
#token correct -> take new password as current password instead of redirecting bla bla

# an Error: Link should be able to be clicked only once.m
class PasswordResetConfirm(GenericAPIView):
	def get(self, request, uidb64, token):
		try:
			user_id=smart_str(urlsafe_base64_decode(uidb64))
			user=User.objects.get(id=user_id)
			if not PasswordResetTokenGenerator().check_token(user, token):
				return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)
			return Response({'success':True, 'message':'credentials is valid', 'uidb64':uidb64, 'token':token}, status=status.HTTP_200_OK)

		except DjangoUnicodeDecodeError:
			return Response({'message':'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)


class SetNewPassword(GenericAPIView):
	serializer_class=SetNewPasswordSerializer
	def patch(self, request):
		serializer=self.serializer_class(data=request.data)
		serializer.is_valid(raise_exception=True)
		return Response({'message':'passwort reset successfull'}, status=status.HTTP_200_OK)
	