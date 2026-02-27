import io
import os
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image


def compress_image(image_field, max_width, max_height, quality=85):
    """
    Compress and resize an ImageField in-place.
    Converts to JPEG for smaller file size. Keeps transparency for PNG if needed.
    """
    img = Image.open(image_field)

    # Convert RGBA/P to RGB for JPEG
    if img.mode in ('RGBA', 'P', 'LA'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = bg
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize if larger than max dimensions (preserves aspect ratio)
    img.thumbnail((max_width, max_height), Image.LANCZOS)

    # Save compressed version
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)

    # Build new filename with .jpg extension
    base_name = os.path.splitext(os.path.basename(image_field.name))[0]
    new_name = f'{base_name}.jpg'
    return ContentFile(output.read(), name=new_name)


class IdeaGenerationRequest(models.Model):
    TOPIC_CHOICES = [
        ('people', 'People'),
        ('events', 'Events'),
        ('places', 'Places'),
        ('culture', 'Culture'),
        ('technology', 'Technology'),
        ('lifestyle', 'Lifestyle'),
        ('business', 'Business'),
        ('health', 'Health & Wellness'),
        ('travel', 'Travel'),
        ('food', 'Food & Cuisine'),
        ('arts', 'Arts & Entertainment'),
        ('sports', 'Sports'),
        ('environment', 'Environment'),
        ('politics', 'Politics'),
        ('science', 'Science'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='idea_requests')
    topics = models.JSONField(help_text='List of selected topic categories')
    additional_context = models.TextField(blank=True, help_text='Additional context or focus area')
    generated_ideas = models.JSONField(blank=True, null=True, help_text='AI-generated ideas list')
    ai_model_used = models.CharField(max_length=30, blank=True, default='claude', help_text='AI model used: claude, openai, auto')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Ideas for {self.user} - {self.created_at.strftime("%Y-%m-%d")}'


class BlogDraft(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('saved', 'Saved'),
        ('published', 'Published to Article'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_drafts')
    idea = models.TextField(help_text='The original idea/prompt')
    title = models.CharField(max_length=300, blank=True)
    generated_content = models.TextField(blank=True)
    edited_content = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    featured_image = models.ImageField(
        upload_to='drafts/images/',
        blank=True,
        null=True,
        help_text='Featured image for the blog post (auto-compressed to max 1200x800)'
    )
    ai_model_used = models.CharField(
        max_length=30, blank=True, default='claude',
        help_text='AI model used: claude, openai, auto'
    )
    linked_article = models.ForeignKey(
        'articles.Article',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ai_draft',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Draft: {self.title or self.idea[:50]} by {self.user}'

    def save(self, *args, **kwargs):
        # Check if a new image was uploaded
        if self.featured_image:
            try:
                old = BlogDraft.objects.get(pk=self.pk)
                image_changed = old.featured_image != self.featured_image
            except BlogDraft.DoesNotExist:
                image_changed = True

            if image_changed:
                compressed = compress_image(self.featured_image, max_width=1200, max_height=800, quality=85)
                self.featured_image.save(compressed.name, compressed, save=False)

        super().save(*args, **kwargs)
