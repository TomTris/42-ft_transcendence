from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
import time


class MyUserManager(BaseUserManager):
    def create_user(self, login, email, date_of_birth, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError("Users must have an email address")
        if not login:
            raise ValueError("Users must have a login")
        if not date_of_birth:
            raise ValueError("Users must have a date of birth")
        
        user = self.model(
            login = login,
            email=self.normalize_email(email),
            date_of_birth=date_of_birth,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, email, date_of_birth, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            login,
            email,
            password=password,
            date_of_birth=date_of_birth,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser):
    login = models.CharField(max_length=40, unique=True)
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    date_of_birth = models.DateField()
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', default='default/default.png')
    elo = models.IntegerField(default=400)
    wins =  models.IntegerField(default=0)
    loses = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    objects = MyUserManager()


    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = ["email", "date_of_birth"]

    def __str__(self):
        return self.login

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
    
