from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from .models import User
from articles.models import Article


@never_cache
@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Magzine, {user.get_full_name()}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@never_cache
@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(['POST'])
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('home')


@login_required
@require_http_methods(['GET', 'POST'])
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)

    user_articles = Article.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'accounts/profile.html', {
        'form': form,
        'user_articles': user_articles,
    })


@login_required
def dashboard_view(request):
    user = request.user
    if user.is_staff:
        recent_articles = Article.objects.all().order_by('-created_at')[:10]
        total_users = User.objects.count()
    else:
        recent_articles = Article.objects.filter(author=user).order_by('-created_at')[:10]
        total_users = None

    published = Article.objects.filter(author=user, status='published').count() if not user.is_staff else Article.objects.filter(status='published').count()
    drafts = Article.objects.filter(author=user, status='draft').count() if not user.is_staff else Article.objects.filter(status='draft').count()

    return render(request, 'accounts/dashboard.html', {
        'recent_articles': recent_articles,
        'total_users': total_users,
        'published_count': published,
        'draft_count': drafts,
    })
