from typing import Any 
# from django.db import models 

from django.contrib.auth.models import (
    AbstractBaseUser, 
    BaseUserManager,
    PermissionsMixin,
)
from django.db.models import EmailField, CharField, BooleanField

EMAIL_MAX_LENGTH = 254
NAME_MAX_LENGTH = 50 
ERROR_EMAIL_REQUIRED = 'Email is required'
ERROR_SUPERUSER_STAFF = 'Superuser must have is_staff=True'
ERROR_SUPERUSER_FLAG = 'Superuser must have is_superuser=False'

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user (
        self,
        email: str, 
        password: str | None = None,
        **extra_fields: Any,
    ) -> 'User':
        if not email:
            raise ValueError(ERROR_EMAIL_REQUIRED)
        email = self.normalize_email(email).lower()
        user = self.model(email = email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)  
        return user

    def create_superuser(
        self, 
        email: str, 
        password: str | None = None,
        **extra_fields: Any,
    )-> 'User':
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields['is_staff'] is not True:
            raise ValueError(ERROR_SUPERUSER_STAFF)
        if extra_fields['is_superuser'] is not True:
            raise ValueError(ERROR_SUPERUSER_FLAG)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = EmailField(
        max_length = EMAIL_MAX_LENGTH, 
        unique = True,
    )
    first_name = CharField(
        max_length = NAME_MAX_LENGTH,
    )
    last_name = CharField(
        max_length = NAME_MAX_LENGTH,
    )
    is_active = BooleanField(
        default = True,
    )
    is_staff = BooleanField(
        default = False,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = UserManager()



