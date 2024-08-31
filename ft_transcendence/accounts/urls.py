from django.urls import path
from .views import (RegisterUserView, VerifyUserEmail, SendRegisterCode,
					LoginUserView, VerifyLoginUserView,
					PasswordResetRequestView, PasswordResetConfirm, SetNewPassword,
					LogoutUserView, HomeView, TokenRefreshView)

urlpatterns=[
	path('register/', RegisterUserView.as_view(), name='register'),
	path('register-verify/', VerifyUserEmail.as_view(), name='register-verify'),
	path('register-send_OTP/', SendRegisterCode.as_view(), name='register-send_OTP'),
	
	path('login/', LoginUserView.as_view(), name='login'),
	path('login-verify/', VerifyLoginUserView.as_view(), name='login-verify'),
	
	path('password_reset-request/', PasswordResetRequestView.as_view(), name='password_reset-request'),
	path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name='password-reset-confirm'),
	path('password_reset-set_new/', SetNewPassword.as_view(), name='password_reset-set_new'),

	
	path('refresh/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
	path('refresh/logout/', LogoutUserView.as_view(), name='logout'),
	path('home/', HomeView.as_view(), name='home'),
	path('', LoginUserView.as_view(), name='login'),
]
