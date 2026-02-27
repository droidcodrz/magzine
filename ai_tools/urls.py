from django.urls import path
from . import views

urlpatterns = [
    path('idea-generator/', views.idea_generator_view, name='idea_generator'),
    path('idea-generator/generate/', views.generate_ideas_ajax, name='generate_ideas'),
    path('blog-generator/', views.blog_generator_view, name='blog_generator'),
    path('blog-generator/generate/', views.generate_draft_ajax, name='generate_draft'),
    path('blog-generator/draft/<int:draft_id>/', views.edit_draft_view, name='edit_draft'),
    path('blog-generator/draft/<int:draft_id>/delete/', views.delete_draft_view, name='delete_draft'),
]
