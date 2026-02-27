from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Article, Category, Tag, Comment
from .forms import ArticleForm, CommentForm


def home_view(request):
    featured = Article.objects.filter(status='published', is_featured=True).order_by('-published_at')[:3]
    latest = Article.objects.filter(status='published').order_by('-published_at')[:9]
    categories = Category.objects.all()
    popular = Article.objects.filter(status='published').order_by('-views')[:5]

    return render(request, 'articles/home.html', {
        'featured_articles': featured,
        'latest_articles': latest,
        'categories': categories,
        'popular_articles': popular,
    })


def article_list_view(request):
    articles = Article.objects.filter(status='published')
    category_slug = request.GET.get('category')
    tag_slug = request.GET.get('tag')
    search_query = request.GET.get('q', '').strip()

    if category_slug:
        articles = articles.filter(category__slug=category_slug)
    if tag_slug:
        articles = articles.filter(tags__slug=tag_slug)
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    articles = articles.order_by('-published_at')
    paginator = Paginator(articles, 12)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    return render(request, 'articles/list.html', {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'search_query': search_query,
        'selected_category': category_slug,
        'selected_tag': tag_slug,
    })


def article_detail_view(request, slug):
    article = get_object_or_404(Article, slug=slug)

    if article.status != 'published':
        if not request.user.is_authenticated:
            return redirect('login')
        if article.author != request.user and not request.user.is_staff:
            return HttpResponseForbidden('You do not have permission to view this article.')

    article.increment_views()

    comment_form = CommentForm()
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to comment.')
            return redirect('login')
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment posted successfully.')
            return redirect('article_detail', slug=slug)

    related = Article.objects.filter(
        status='published',
        category=article.category
    ).exclude(pk=article.pk)[:3]

    return render(request, 'articles/detail.html', {
        'article': article,
        'comment_form': comment_form,
        'comments': article.comments.filter(is_approved=True),
        'related_articles': related,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def article_create_view(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            if article.status == 'published' and not article.published_at:
                article.published_at = timezone.now()
            article.save()
            form.save()  # to handle M2M tags
            messages.success(request, 'Article created successfully.')
            return redirect('article_detail', slug=article.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ArticleForm()

    return render(request, 'articles/create.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def article_edit_view(request, slug):
    article = get_object_or_404(Article, slug=slug)

    if article.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden('You do not have permission to edit this article.')

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save(commit=False)
            if article.status == 'published' and not article.published_at:
                article.published_at = timezone.now()
            article.save()
            form.save()
            messages.success(request, 'Article updated successfully.')
            return redirect('article_detail', slug=article.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial_tags = ', '.join([tag.name for tag in article.tags.all()])
        form = ArticleForm(instance=article, initial={'tags_input': initial_tags})

    return render(request, 'articles/edit.html', {'form': form, 'article': article})


@login_required
@require_POST
def article_delete_view(request, slug):
    article = get_object_or_404(Article, slug=slug)

    if article.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden('You do not have permission to delete this article.')

    article.delete()
    messages.success(request, 'Article deleted successfully.')
    return redirect('dashboard')


def dashboard_redirect(request):
    return redirect('dashboard')
