import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from .models import IdeaGenerationRequest, BlogDraft
from .services import (
    generate_article_ideas, generate_blog_draft,
    MODEL_CLAUDE, MODEL_OPENAI, MODEL_AUTO,
)
from articles.models import Article, Category


TOPIC_CHOICES = [
    ('people',      'People',               'bi-person-fill'),
    ('events',      'Events',               'bi-calendar-event-fill'),
    ('places',      'Places',               'bi-geo-alt-fill'),
    ('culture',     'Culture',              'bi-palette-fill'),
    ('technology',  'Technology',           'bi-cpu-fill'),
    ('lifestyle',   'Lifestyle',            'bi-heart-fill'),
    ('business',    'Business',             'bi-briefcase-fill'),
    ('health',      'Health & Wellness',    'bi-heart-pulse-fill'),
    ('travel',      'Travel',               'bi-airplane-fill'),
    ('food',        'Food & Cuisine',       'bi-egg-fried'),
    ('arts',        'Arts & Entertainment', 'bi-music-note-beamed'),
    ('sports',      'Sports',               'bi-trophy-fill'),
    ('environment', 'Environment',          'bi-tree-fill'),
    ('science',     'Science',              'bi-flask-fill'),
]

VALID_TOPICS = {t[0] for t in TOPIC_CHOICES}
VALID_MODELS = {MODEL_CLAUDE, MODEL_OPENAI, MODEL_AUTO}


@login_required
def idea_generator_view(request):
    if request.user.is_staff:
        recent_requests = IdeaGenerationRequest.objects.select_related('user').order_by('-created_at')[:10]
    else:
        recent_requests = IdeaGenerationRequest.objects.filter(user=request.user)[:5]

    preselected_topics = []
    topics_param = request.GET.get('topics', '')
    if topics_param:
        preselected_topics = [t.strip() for t in topics_param.split(',') if t.strip() in VALID_TOPICS]

    return render(request, 'ai_tools/idea_generator.html', {
        'topic_choices': TOPIC_CHOICES,
        'recent_requests': recent_requests,
        'preselected_topics': json.dumps(preselected_topics),
        'is_admin': request.user.is_staff,
    })


@login_required
@require_POST
def generate_ideas_ajax(request):
    try:
        data = json.loads(request.body)
        topics = data.get('topics', [])
        additional_context = data.get('context', '').strip()
        model = data.get('model', MODEL_CLAUDE)

        if not topics:
            return JsonResponse({'error': 'Please select at least one topic.'}, status=400)
        if len(topics) > 8:
            return JsonResponse({'error': 'Please select at most 8 topics.'}, status=400)
        for topic in topics:
            if topic not in VALID_TOPICS:
                return JsonResponse({'error': f'Invalid topic: {topic}'}, status=400)
        if additional_context and len(additional_context) > 500:
            return JsonResponse({'error': 'Additional context is too long.'}, status=400)
        if model not in VALID_MODELS:
            model = MODEL_CLAUDE

        ideas = generate_article_ideas(topics, additional_context, model=model)

        IdeaGenerationRequest.objects.create(
            user=request.user,
            topics=topics,
            additional_context=additional_context,
            generated_ideas=ideas,
            ai_model_used=model,
        )

        return JsonResponse({'ideas': ideas, 'model_used': model})

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except Exception:
        return JsonResponse({'error': 'Failed to generate ideas. Please try again.'}, status=500)


@login_required
def blog_generator_view(request):
    if request.user.is_staff:
        drafts = BlogDraft.objects.select_related('user').order_by('-created_at')[:10]
    else:
        drafts = BlogDraft.objects.filter(user=request.user)[:10]

    return render(request, 'ai_tools/blog_generator.html', {'drafts': drafts})


@login_required
@require_POST
def generate_draft_ajax(request):
    try:
        data = json.loads(request.body)
        idea = data.get('idea', '').strip()
        model = data.get('model', MODEL_CLAUDE)

        if not idea:
            return JsonResponse({'error': 'Please provide an idea or topic.'}, status=400)
        if len(idea) < 10:
            return JsonResponse({'error': 'Idea is too short. Please provide more detail.'}, status=400)
        if len(idea) > 1000:
            return JsonResponse({'error': 'Idea is too long. Please keep it under 1000 characters.'}, status=400)
        if model not in VALID_MODELS:
            model = MODEL_CLAUDE

        result = generate_blog_draft(idea, model=model)

        draft = BlogDraft.objects.create(
            user=request.user,
            idea=idea,
            title=result.get('title', ''),
            generated_content=result.get('content', ''),
            edited_content=result.get('content', ''),
            status='draft',
            ai_model_used=model,
        )

        return JsonResponse({
            'draft_id': draft.id,
            'title': draft.title,
            'excerpt': result.get('excerpt', ''),
            'content': draft.generated_content,
            'model_used': model,
        })

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except Exception:
        return JsonResponse({'error': 'Failed to generate draft. Please try again.'}, status=500)


@login_required
def edit_draft_view(request, draft_id):
    if request.user.is_staff:
        draft = get_object_or_404(BlogDraft, id=draft_id)
    else:
        draft = get_object_or_404(BlogDraft, id=draft_id, user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        action = request.POST.get('action', 'save')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect('edit_draft', draft_id=draft.id)
        if not content:
            messages.error(request, 'Content is required.')
            return redirect('edit_draft', draft_id=draft.id)

        draft.title = title
        draft.edited_content = content

        if 'featured_image' in request.FILES:
            draft.featured_image = request.FILES['featured_image']

        if action == 'publish':
            category_id = request.POST.get('category')
            category = None
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    pass

            article = Article.objects.create(
                title=title,
                content=content,
                excerpt=request.POST.get('excerpt', '')[:500],
                author=request.user,
                category=category,
                status='draft',
                ai_generated=True,
            )
            if draft.featured_image:
                article.cover_image = draft.featured_image
                article.save()

            draft.status = 'published'
            draft.linked_article = article
            draft.save()
            messages.success(request, 'Draft published as article.')
            return redirect('article_edit', slug=article.slug)
        else:
            draft.status = 'saved'
            draft.save()
            messages.success(request, 'Draft saved successfully.')
            return redirect('edit_draft', draft_id=draft.id)

    return render(request, 'ai_tools/edit_draft.html', {
        'draft': draft,
        'categories': Category.objects.all(),
    })


@login_required
@require_POST
def delete_draft_view(request, draft_id):
    if request.user.is_staff:
        draft = get_object_or_404(BlogDraft, id=draft_id)
    else:
        draft = get_object_or_404(BlogDraft, id=draft_id, user=request.user)
    draft.delete()
    messages.success(request, 'Draft deleted.')
    return redirect('manage_blogs')


@login_required
def manage_blogs_view(request):
    if request.user.is_staff:
        drafts = BlogDraft.objects.select_related('user', 'linked_article').order_by('-created_at')
    else:
        drafts = BlogDraft.objects.filter(user=request.user).select_related('linked_article').order_by('-created_at')

    return render(request, 'ai_tools/manage_blogs.html', {
        'drafts': drafts,
        'is_admin': request.user.is_staff,
    })


@login_required
def manage_ideas_view(request):
    if request.user.is_staff:
        idea_requests = IdeaGenerationRequest.objects.select_related('user').order_by('-created_at')
    else:
        idea_requests = IdeaGenerationRequest.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'ai_tools/manage_ideas.html', {
        'idea_requests': idea_requests,
        'is_admin': request.user.is_staff,
    })
