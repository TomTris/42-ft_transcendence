import random
from django.core.mail import EmailMessage, send_mail
from .models import User, OneTimePassword, OneTimePasswordLogin
from django.conf import settings

def generateOtp():
	otp=""
	for i in range(10):
		otp += str(random.randint(1, 9))
	return otp

def send_code_to_user(email):
	Subject="One time passcode for Email verification"
	
	otp_code=generateOtp()
	print(otp_code)
	user=User.objects.get(email=email)
	email_body=f"Hi {user.first_name} thanks for signing up on our Pingpong\nPlease verify your email with the following one time passcode {otp_code}"
	from_email=settings.EMAIL_HOST_USER
	if OneTimePassword.objects.filter(user=user).exists():
		user_del = OneTimePassword.objects.filter(email=email).first()
		user_del.delete()
	OneTimePassword.objects.create(user=user, code=otp_code, email=email, times=0)
	# send_mail( Subject, email_body, from_email, [email], False)


def send_code_to_user_login(email):
	Subject="One time passcode for Email verification"
	otp_code=generateOtp()
	print(otp_code)
	user=User.objects.get(email=email)
	email_body=f"Hi, Please use this code to login\n{otp_code}"
	from_email=settings.EMAIL_HOST_USER
	if OneTimePasswordLogin.objects.filter(user=user).exists():
		user_del = OneTimePasswordLogin.objects.get(email=email)
		user_del.delete()
	OneTimePasswordLogin.objects.create(user=user, code=otp_code, email=email, times=0)
	# send_mail( Subject, email_body, from_email, [email], False)



def send_normal_email(data):
	subject=data['email_subject']
	body=data['email_body']
	from_email=settings.EMAIL_HOST_USER
	to_email=data['to_email']
	print(body)
	# send_mail( subject, body, from_email, [to_email], False)