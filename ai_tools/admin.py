from django.contrib import admin
from .models import IdeaGenerationRequest, BlogDraft


@admin.register(IdeaGenerationRequest)
class IdeaGenerationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'topics', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)


@admin.register(BlogDraft)
class BlogDraftAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'title', 'idea')
    readonly_fields = ('created_at', 'updated_at')
