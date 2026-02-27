from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('articles/', views.article_list_view, name='article_list'),
    path('articles/new/', views.article_create_view, name='article_create'),
    path('articles/<slug:slug>/', views.article_detail_view, name='article_detail'),
    path('articles/<slug:slug>/edit/', views.article_edit_view, name='article_edit'),
    path('articles/<slug:slug>/delete/', views.article_delete_view, name='article_delete'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
]
