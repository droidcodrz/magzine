from django.contrib import admin
from .models import Article, Category, Tag, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'ai_generated', 'views', 'created_at')
    list_filter = ('status', 'is_featured', 'ai_generated', 'category', 'created_at')
    search_fields = ('title', 'author__email', 'content')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'created_at'
    filter_horizontal = ('tags',)
    readonly_fields = ('views', 'created_at', 'updated_at')

    actions = ['publish_articles', 'archive_articles']

    def publish_articles(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status__in=['draft', 'review']).update(status='published', published_at=timezone.now())
        self.message_user(request, f'{count} articles published.')
    publish_articles.short_description = 'Publish selected articles'

    def archive_articles(self, request, queryset):
        count = queryset.update(status='archived')
        self.message_user(request, f'{count} articles archived.')
    archive_articles.short_description = 'Archive selected articles'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'article', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('author__email', 'content', 'article__title')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f'{count} comments approved.')
    approve_comments.short_description = 'Approve selected comments'
