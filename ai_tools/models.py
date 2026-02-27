from django.db import models
from django.conf import settings


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
