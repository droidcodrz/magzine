from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ROLE_CHOICES = [
        ('reader', 'Reader'),
        ('writer', 'Writer'),
        ('editor', 'Editor'),
    ]

    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='reader')
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username

    @property
    def is_writer(self):
        return self.role in ('writer', 'editor') or self.is_staff

    @property
    def is_editor(self):
        return self.role == 'editor' or self.is_staff
