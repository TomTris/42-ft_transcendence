
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from users.models import User
from users.models import User
from django.core.mail import EmailMessage, send_mail
from django.conf import settings


with open('/app/users/send_to_subscribers.txt', 'r') as file:
	lines = file.readlines()
	if len(lines) <= 1:
		print("The file should have at least 1 line for Subject")
	else:
		subject = lines[0].strip()
		body = ''.join(lines[1:]).strip()
		from_email=settings.EMAIL_HOST_USER
		subscribed_users = User.objects.filter(is_subscribe=True)
		for user in subscribed_users:
			to_email = user.email
			send_mail(subject, body, from_email, [to_email], fail_silently=False)