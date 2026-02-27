import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import IdeaGenerationRequest, BlogDraft
from .services import generate_article_ideas, generate_blog_draft
from articles.models import Article, Category


TOPIC_CHOICES = [
    ('people', 'People', 'bi-person-fill'),
    ('events', 'Events', 'bi-calendar-event-fill'),
    ('places', 'Places', 'bi-geo-alt-fill'),
    ('culture', 'Culture', 'bi-palette-fill'),
    ('technology', 'Technology', 'bi-cpu-fill'),
    ('lifestyle', 'Lifestyle', 'bi-heart-fill'),
    ('business', 'Business', 'bi-briefcase-fill'),
    ('health', 'Health & Wellness', 'bi-heart-pulse-fill'),
    ('travel', 'Travel', 'bi-airplane-fill'),
    ('food', 'Food & Cuisine', 'bi-egg-fried'),
    ('arts', 'Arts & Entertainment', 'bi-music-note-beamed'),
    ('sports', 'Sports', 'bi-trophy-fill'),
    ('environment', 'Environment', 'bi-tree-fill'),
    ('science', 'Science', 'bi-flask-fill'),
]


@login_required
def idea_generator_view(request):
    """Page for generating article ideas based on topic selection."""
    recent_requests = IdeaGenerationRequest.objects.filter(user=request.user)[:5]
    return render(request, 'ai_tools/idea_generator.html', {
        'topic_choices': TOPIC_CHOICES,
        'recent_requests': recent_requests,
    })


@login_required
@require_POST
def generate_ideas_ajax(request):
    """AJAX endpoint to generate ideas."""
    try:
        data = json.loads(request.body)
        topics = data.get('topics', [])
        additional_context = data.get('context', '').strip()

        if not topics:
            return JsonResponse({'error': 'Please select at least one topic.'}, status=400)

        if len(topics) > 8:
            return JsonResponse({'error': 'Please select at most 8 topics.'}, status=400)

        # Validate topics against allowed choices
        valid_topics = {t[0] for t in TOPIC_CHOICES}
        for topic in topics:
            if topic not in valid_topics:
                return JsonResponse({'error': f'Invalid topic: {topic}'}, status=400)

        if additional_context and len(additional_context) > 500:
            return JsonResponse({'error': 'Additional context is too long.'}, status=400)

        ideas = generate_article_ideas(topics, additional_context)

        # Save the request
        IdeaGenerationRequest.objects.create(
            user=request.user,
            topics=topics,
            additional_context=additional_context,
            generated_ideas=ideas,
        )

        return JsonResponse({'ideas': ideas})

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except Exception as e:
        return JsonResponse({'error': 'Failed to generate ideas. Please try again.'}, status=500)


@login_required
def blog_generator_view(request):
    """Page for generating blog drafts from ideas."""
    drafts = BlogDraft.objects.filter(user=request.user)[:10]
    return render(request, 'ai_tools/blog_generator.html', {
        'drafts': drafts,
    })


@login_required
@require_POST
def generate_draft_ajax(request):
    """AJAX endpoint to generate a blog draft."""
    try:
        data = json.loads(request.body)
        idea = data.get('idea', '').strip()

        if not idea:
            return JsonResponse({'error': 'Please provide an idea or topic.'}, status=400)

        if len(idea) < 10:
            return JsonResponse({'error': 'Idea is too short. Please provide more detail.'}, status=400)

        if len(idea) > 1000:
            return JsonResponse({'error': 'Idea is too long. Please keep it under 1000 characters.'}, status=400)

        result = generate_blog_draft(idea)

        draft = BlogDraft.objects.create(
            user=request.user,
            idea=idea,
            title=result.get('title', ''),
            generated_content=result.get('content', ''),
            edited_content=result.get('content', ''),
            status='draft',
        )

        return JsonResponse({
            'draft_id': draft.id,
            'title': draft.title,
            'excerpt': result.get('excerpt', ''),
            'content': draft.generated_content,
        })

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except Exception as e:
        return JsonResponse({'error': 'Failed to generate draft. Please try again.'}, status=500)


@login_required
def edit_draft_view(request, draft_id):
    """Edit and save a generated draft."""
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

        if action == 'publish':
            # Create a new article from this draft
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
            draft.status = 'published'
            draft.linked_article = article
            draft.save()
            messages.success(request, 'Draft published as article. You can now edit and publish it.')
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
    draft = get_object_or_404(BlogDraft, id=draft_id, user=request.user)
    draft.delete()
    messages.success(request, 'Draft deleted.')
    return redirect('manage_blogs')


@login_required
def manage_blogs_view(request):
    """List all blog drafts for the current user."""
    drafts = BlogDraft.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'ai_tools/manage_blogs.html', {'drafts': drafts})


@login_required
def manage_ideas_view(request):
    """List all idea generation requests for the current user."""
    idea_requests = IdeaGenerationRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'ai_tools/manage_ideas.html', {'idea_requests': idea_requests})
