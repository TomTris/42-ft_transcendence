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
    token_reset_password=models.CharField(max_length=100, verbose_name=_("Last Name"), default='')

    is_online=models.BooleanField(default=False)
    online_check=models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', default='default/default.png')
    elo = models.IntegerField(default=400)
    wins =  models.IntegerField(default=0)
    loses = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    username = models.CharField(max_length=40)

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
        print()
        print("refrsh = ", refresh)
        print()
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


# from django.db import models
# from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
# import time


# class MyUserManager(BaseUserManager):
#     def create_user(self, username, login, email, date_of_birth, password=None):
#         """
#         Creates and saves a User with the given email, date of
#         birth and password.
#         """
#         if not username:
#             raise ValueError('Users must have a username')
#         if not email:
#             raise ValueError("Users must have an email address")
#         if not login:
#             raise ValueError("Users must have a login")
#         if not date_of_birth:
#             raise ValueError("Users must have a date of birth")
        
#         user = self.model(
#             username=username,
#             login=login,
#             email=self.normalize_email(email),
#             date_of_birth=date_of_birth,
#         )
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, username, login, email, date_of_birth, password=None):
#         """
#         Creates and saves a superuser with the given email, date of
#         birth and password.
#         """
#         user = self.create_user(
#             username,
#             login,
#             email,
#             password=password,
#             date_of_birth=date_of_birth,
#         )
#         user.is_admin = True
#         user.save(using=self._db)
#         return user


# class MyUser(AbstractBaseUser):
#     login = models.CharField(max_length=40, unique=True)
#     email = models.EmailField(
#         verbose_name="email address",
#         max_length=255,
#         unique=True,
#     )
#     date_of_birth = models.DateField()
    
#     is_active = models.BooleanField(default=True)
#     is_admin = models.BooleanField(default=False)

#     objects = MyUserManager()


#     USERNAME_FIELD = "login"
#     REQUIRED_FIELDS = ["email", "date_of_birth", "username"]

#     def __str__(self):
#         return self.login

#     def has_perm(self, perm, obj=None):
#         "Does the user have a specific permission?"
#         # Simplest possible answer: Yes, always
#         return True

#     def has_module_perms(self, app_label):
#         "Does the user have permissions to view the app `app_label`?"
#         # Simplest possible answer: Yes, always
#         return True

#     @property
#     def is_staff(self):
#         "Is the user a member of staff?"
#         # Simplest possible answer: All admins are staff
#         return self.is_admin
    
