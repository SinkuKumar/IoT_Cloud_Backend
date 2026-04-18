from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email as the primary identifier.
    Username is optional and can also be used for login alongside email.
    """

    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(
        max_length=150, unique=True, null=True, blank=True, db_index=True
    )

    is_active = models.BooleanField(default=False)  # inactive until email verified
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # only email + password needed for createsuperuser

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.username or self.email

    def get_short_name(self):
        return self.username or self.email.split("@")[0]
