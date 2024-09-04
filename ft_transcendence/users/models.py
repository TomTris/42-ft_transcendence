from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .managers import UserManager
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
# Create your models here.

class User(AbstractBaseUser, PermissionsMixin):
    email=models.EmailField(max_length=255, unique=True, verbose_name=_("Email Address"))
    first_name=models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name=models.CharField(max_length=100, verbose_name=_("Last Name"))
    is_staff = models.BooleanField(default=False)
    is_superuser=models.BooleanField(default=False)
    is_verified=models.BooleanField(default=False)
    date_joined=models.DateTimeField(auto_now_add=True)
    last_login=models.DateTimeField(auto_now=True)
    twoFaEnable=models.BooleanField(default=True)

    avatar = models.ImageField(upload_to='avatars/', default='/default/default.png', blank=True, null=True)
    # is_subscribe = models.BooleanField(default=True)

    is_online=models.BooleanField(default=False)
    online_check=models.BooleanField(default=True)
    elo = models.IntegerField(default=400)
    wins =  models.IntegerField(default=0)
    loses = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    username = models.CharField(max_length=40)
    is_playing = models.BooleanField(default=False)

    USERNAME_FIELD="email"
    REQUIRED_FIELDS= ["first_name", "last_name"]
    objects= UserManager()

    def __str__(self):
        return self.email
    
    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def tokens(self):
        refresh=RefreshToken.for_user(self)
        return {
            'refresh':str(refresh),
            'access':str(refresh.access_token)
        }

class OneTimePassword(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    email=models.EmailField(max_length=255, unique=True, default='')
    code=models.CharField(max_length=10, default='')
    times=models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.first_name}-passcode"

    @classmethod
    def delete_for_user(cls, user):
        try:
            otp = cls.objects.get(user=user)
            otp.delete()
            return True
        except cls.DoesNotExist:
            return True

class OneTimePasswordLogin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email=models.EmailField(max_length=255, unique=True, default='')
    code=models.CharField(max_length=10, default='')
    times=models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.first_name}-passcode"

    @classmethod
    def delete_for_user(cls, user):
        try:
            otp = cls.objects.get(user=user)
            otp.delete()
            return True
        except cls.DoesNotExist:
            return True


class OneTimePasswordReset(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email=models.EmailField(max_length=255, unique=True, default='')
    reset_token=models.CharField(max_length=200, default='')
    times=models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.first_name}-passcode"

    @classmethod
    def delete_for_user(cls, user):
        try:
            otp = cls.objects.get(user=user)
            otp.delete()
            return True
        except cls.DoesNotExist:
            return True



class Friendship(models.Model):
    person1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='person1', null=True, on_delete=models.SET_NULL)
    person2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='person2', null=True, on_delete=models.SET_NULL)

