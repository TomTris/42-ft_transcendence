from .models import User, OneTimePasswordReset, OneTimePasswordLogin
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.encoding import smart_str, smart_bytes, force_str
from .utils import send_normal_email, send_code_to_user_login
from rest_framework_simplejwt.tokens import RefreshToken, TokenError



class UserRegisterSerializer(serializers.ModelSerializer):
	password=serializers.CharField(max_length=68, min_length=6, write_only=True)
	password2=serializers.CharField(max_length=68, min_length=6, write_only=True)

	class Meta:
		model=User
		fields=['email', 'first_name', 'last_name', 'password', 'password2']
	
	def validate(self, attrs):
		email=attrs.get('email')
		if email is None:
			raise serializers.ValidationError("Email is not valid")
		if User.objects.filter(email=email).exists():
			raise serializers.ValidationError("Email has been used")
		password = attrs.get('password', '')
		password2 = attrs.get('password2', '')
		if password != password2 or password == '':
			raise serializers.ValidationError("passwords do not match")
		return attrs
	
	def create(self, validated_data):
		user=User.objects.create_user(
			email=validated_data['email'],
			first_name=validated_data.get('first_name'),
			last_name=validated_data.get('last_name'),
			password=validated_data.get('password'),
			twoFaEnable=True,
		)
		return user





class LoginSerializer(serializers.ModelSerializer):
	email=serializers.EmailField(max_length=255, min_length=6)
	password=serializers.CharField(max_length=68, write_only=True)

	class Meta:
		model = User
		fields=['email', 'password']

	def validate(self, attrs):
		email=attrs.get('email', '')
		password=attrs.get('password', '')
		request=self.context.get('request', '')
		user=authenticate(request, email=email, password=password)
		if not user:
			raise AuthenticationFailed("Invalid credentials, please try again")
		if not user.is_verified:
			raise AuthenticationFailed("Email is not verified")
		return email

class VerifyLoginSerializer(serializers.Serializer):
	email=serializers.EmailField(max_length=255, min_length=6)
	otp=serializers.CharField(max_length=20, write_only=True)

	class Meta:
		model = User
		fields=['email', 'otp']

	def validate(self, attrs):
		otpcode=attrs.get('otp', '')
		email=attrs.get('email', '')
		request=self.context.get('request')
		if email == '' or otpcode == '':
			raise AuthenticationFailed("Email and OTP are required")
		try:
			user_row = OneTimePasswordLogin.objects.get(email=email)
		except:
			raise AuthenticationFailed("code or email is invalid")
		if user_row.code == otpcode:
			OneTimePasswordLogin.delete_for_user(user=user_row.user)
			data={
				'email_body':"You have just loggined",
				'email_subject':"Your Login",
				'to_email':email
			}
			send_normal_email(data)
			user=User.objects.get(email=email)
			user_tokens=user.tokens()
			return {
				'email': user.email,
				'full_name': user.get_full_name,
				'access_token': str(user_tokens.get('access')),
				'refresh_token': str(user_tokens.get('refresh')),
				'redirect_url': reverse('home')
				}
		
		if user_row.times == 2:
			OneTimePasswordLogin.delete_for_user(user=user_row.user)
			raise AuthenticationFailed("code is invalid. You tried already 3 times with the same Email.\n\
				The code sent to you is since now invalid.\n\
				Please login again and try again")
		user_row.times += 1
		user_row.save()
		raise AuthenticationFailed("code or email is invalid")




class PasswordResetRequestSerializer(serializers.Serializer):
	email=serializers.EmailField(max_length=255)

	class Meta:
		fields=['email']
	
	def validate(self, attrs):
		email=attrs.get('email', '')
		if User.objects.filter(email=email).exists():
			user=User.objects.get(email=email)
			uidb64=urlsafe_base64_encode(smart_bytes(user.id))
			token=PasswordResetTokenGenerator().make_token(user)
			try:
				user_OneTimePasswordReset = OneTimePasswordReset.objects.get(user=user)
				user_OneTimePasswordReset.delete_for_user(user=user)
			except Exception as e:
				pass
			OneTimePasswordReset.objects.create(user=user, reset_token=token, email=email, times=0)
			request=self.context.get('request')
			site_domain=get_current_site(request).domain
			relative_link=reverse('password-reset-confirm', kwargs={'uidb64':uidb64, 'token':token})
			abslink=f"https://{site_domain}{relative_link}"
			email_body=f"Hi use the link below to reset your password \n {abslink}"
			data={
				'email_body':email_body,
				'email_subject':"Reset your Password",
				'to_email':user.email
			}
			send_normal_email(data)
			return attrs
		else:
			raise AuthenticationFailed("Email not exists", 400)


class SetNewPasswordSerializer(serializers.Serializer):
	password=serializers.CharField(max_length=100, min_length=6, write_only=True)
	confirm_password=serializers.CharField(max_length=100, min_length=6, write_only=True)
	uidb64=serializers.CharField(write_only=True)
	token=serializers.CharField(write_only=True)

	class Meta:
		fields=["password", "confirm_password", "uidb64", "token"]

	def validate(self, attrs):
		try:
			token=attrs.get('token', '')
			uidb64=attrs.get('uidb64', '')
			password=attrs.get('password', '')
			confirm_password=attrs.get('confirm_password', '')

			user_id=force_str(urlsafe_base64_decode(uidb64))
			user=User.objects.get(id=user_id)
			user_OneTimePasswordReset = OneTimePasswordReset.objects.get(user=user)
			if not PasswordResetTokenGenerator().check_token(user, token) \
				or user_OneTimePasswordReset.reset_token != token:
				raise AuthenticationFailed("reset link is invalid or has expired", 401)
			if password != confirm_password or password == '':
				raise AuthenticationFailed("Passwords don't match", 401)
			user.set_password(password)
			user.save()
			user_OneTimePasswordReset.delete_for_user()
			return user
		except User.DoesNotExist:
			raise AuthenticationFailed("Reset link is invalid or has expired", 401)
		except OneTimePasswordReset.DoesNotExist:
			raise AuthenticationFailed("Reset link is invalid or has expired", 401)



class LogoutUserSeriallizer(serializers.Serializer):
	refresh_token=serializers.CharField()
	default_error_messages={
		'bad_token':('Token is Invalid or has expired')
	}
	
	def validate(self, attrs):
		self.token=attrs.get('refresh_token')
		return attrs

	def save(self, **kwargs):
		try:
			token=RefreshToken(self.token)
			token.blacklist()
		except TokenError:
			return self.fail('bad_token')




class TrashSerializer(serializers.ModelSerializer):
	otp=serializers.CharField(max_length=68, min_length=6, write_only=True)

	class Meta:
		model=User
		fields = '__all__'

	def validate(self, attrs):
		return attrs


