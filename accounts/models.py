import io
import os
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile
from PIL import Image


def compress_avatar(image_field, size=400, quality=85):
    """Resize and compress user avatar to a square-cropped JPEG."""
    img = Image.open(image_field)

    # Convert to RGB
    if img.mode in ('RGBA', 'P', 'LA'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = bg
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Crop to square from center
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))

    # Resize to target size
    img = img.resize((size, size), Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)

    base_name = os.path.splitext(os.path.basename(image_field.name))[0]
    return ContentFile(output.read(), name=f'{base_name}.jpg')


class User(AbstractUser):
    ROLE_CHOICES = [
        ('reader', 'Reader'),
        ('writer', 'Writer'),
        ('editor', 'Editor'),
    ]

    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='reader')
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='Profile picture (auto-compressed to 400x400 JPEG)'
    )
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

    def save(self, *args, **kwargs):
        if self.avatar:
            try:
                old = User.objects.get(pk=self.pk)
                avatar_changed = old.avatar != self.avatar
            except User.DoesNotExist:
                avatar_changed = True

            if avatar_changed:
                compressed = compress_avatar(self.avatar, size=400, quality=85)
                self.avatar.save(compressed.name, compressed, save=False)

        super().save(*args, **kwargs)
