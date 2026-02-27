from django.urls import path
from . import views

urlpatterns = [
    # Idea Generator
    path('idea-generator/',             views.idea_generator_view,      name='idea_generator'),
    path('idea-generator/generate/',    views.generate_ideas_ajax,      name='generate_ideas'),
    path('idea-generator/manage/',      views.manage_ideas_view,        name='manage_ideas'),

    # Trending Ideas (admin only)
    path('idea-generator/trending/',          views.trending_ideas_view,     name='trending_ideas'),
    path('idea-generator/trending/generate/', views.generate_trending_ajax,  name='generate_trending'),

    # Blog Generator — multi-step
    path('blog-generator/',                             views.blog_generator_view,    name='blog_generator'),
    path('blog-generator/outline/',                     views.generate_outline_ajax,  name='generate_outline'),
    path('blog-generator/generate/',                    views.generate_draft_ajax,    name='generate_draft'),
    path('blog-generator/draft/<int:draft_id>/',        views.edit_draft_view,        name='edit_draft'),
    path('blog-generator/draft/<int:draft_id>/delete/', views.delete_draft_view,      name='delete_draft'),
    path('blog-generator/draft/<int:draft_id>/image/',  views.generate_image_ajax,    name='generate_image'),
    path('blog-generator/draft/<int:draft_id>/docx/',   views.download_draft_docx,    name='download_docx'),
    path('blog-generator/draft/<int:draft_id>/pdf/',    views.download_draft_pdf,     name='download_pdf'),
    path('blog-generator/manage/',                      views.manage_blogs_view,      name='manage_blogs'),
]
