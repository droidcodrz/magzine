import json
import re
import requests
import anthropic
import openai as openai_lib
from django.conf import settings


# ---------------------------------------------------------------------------
# Model constants
# ---------------------------------------------------------------------------
MODEL_CLAUDE  = 'claude'
MODEL_OPENAI  = 'openai'
MODEL_GEMINI  = 'gemini'
MODEL_AUTO    = 'auto'

CLAUDE_MODEL  = 'claude-sonnet-4-6'
OPENAI_MODEL  = 'gpt-4o'
GEMINI_MODEL  = 'gemini-1.5-pro'

AUTO_BLOG_MODEL  = MODEL_CLAUDE
AUTO_IDEAS_MODEL = MODEL_OPENAI


def _resolve_model(selected: str, task: str) -> str:
    """Resolve 'auto' to actual provider based on task and available API keys."""
    if selected == MODEL_AUTO:
        preferred = AUTO_BLOG_MODEL if task == 'blog' else AUTO_IDEAS_MODEL
        if preferred == MODEL_OPENAI and not settings.OPENAI_API_KEY:
            return MODEL_CLAUDE
        if preferred == MODEL_CLAUDE and not settings.ANTHROPIC_API_KEY:
            return MODEL_OPENAI if settings.OPENAI_API_KEY else MODEL_GEMINI
        return preferred
    if selected == MODEL_GEMINI and not getattr(settings, 'GOOGLE_API_KEY', ''):
        return MODEL_CLAUDE
    return selected


def _get_anthropic():
    key = settings.ANTHROPIC_API_KEY
    if not key:
        raise ValueError('ANTHROPIC_API_KEY is not configured. Please add it to your .env file.')
    return anthropic.Anthropic(api_key=key)


def _get_openai():
    key = settings.OPENAI_API_KEY
    if not key:
        raise ValueError('OPENAI_API_KEY is not configured. Please add it to your .env file.')
    return openai_lib.OpenAI(api_key=key)


def _get_gemini():
    try:
        import google.generativeai as genai
    except ImportError:
        raise ValueError('google-generativeai package not installed. Run: pip install google-generativeai')
    key = getattr(settings, 'GOOGLE_API_KEY', '')
    if not key:
        raise ValueError('GOOGLE_API_KEY is not configured. Please add it to your .env file.')
    genai.configure(api_key=key)
    return genai.GenerativeModel(GEMINI_MODEL)


def _extract_json_list(text: str) -> list:
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


def _extract_json_object(text: str) -> dict:
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


def _call_llm(prompt: str, provider: str, max_tokens: int = 2048, json_mode: bool = True) -> str:
    """Unified LLM call that returns raw text."""
    if provider == MODEL_OPENAI:
        client = _get_openai()
        kwargs = {'model': OPENAI_MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens}
        if json_mode:
            kwargs['response_format'] = {'type': 'json_object'}
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    elif provider == MODEL_GEMINI:
        model = _get_gemini()
        response = model.generate_content(prompt)
        return response.text
    else:
        client = _get_anthropic()
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return message.content[0].text


# ---------------------------------------------------------------------------
# 1. Generate Article Ideas
# ---------------------------------------------------------------------------

def generate_article_ideas(topics: list, additional_context: str = '', model: str = MODEL_CLAUDE) -> list:
    """Generate 8 magazine article ideas based on selected topics."""
    provider = _resolve_model(model, task='ideas')
    topics_str = ', '.join(topics)
    context_str = f'\nAdditional focus: {additional_context}' if additional_context else ''

    prompt = f"""You are a creative magazine editor for a modern, sophisticated magazine.
Generate 8 compelling, original magazine article ideas for these topic categories: {topics_str}.{context_str}

Return ONLY a JSON array (no extra text):
[
  {{
    "title": "Catchy article title",
    "description": "2-3 sentence description of what the article covers",
    "angle": "The unique hook or angle that makes this interesting",
    "audience": "Target reader description"
  }}
]

Make the ideas diverse, timely, and genuinely engaging."""

    text = _call_llm(prompt, provider, max_tokens=2048, json_mode=True)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        for key in ('ideas', 'articles', 'results', 'items'):
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        return list(parsed.values())[0]
    except Exception:
        return _extract_json_list(text)


# ---------------------------------------------------------------------------
# 2. Generate SEO Blog Outline
# ---------------------------------------------------------------------------

def generate_blog_outline(topic: str, model: str = MODEL_CLAUDE) -> dict:
    """Generate an SEO-optimised blog outline with keywords and headline structure."""
    provider = _resolve_model(model, task='blog')

    prompt = f"""You are an expert SEO content strategist and magazine editor.

Generate a detailed, SEO-optimised blog outline for this topic: "{topic}"

Return ONLY a JSON object with this exact structure:
{{
  "title": "SEO-optimised H1 title (50-60 characters, includes primary keyword)",
  "meta_description": "Compelling meta description 150-160 characters with primary keyword",
  "focus_keywords": ["primary keyword", "secondary keyword", "long-tail phrase 1", "long-tail phrase 2", "long-tail phrase 3"],
  "word_count_target": 850,
  "tone": "informative",
  "sections": [
    {{
      "h2": "Section heading (use focus keywords naturally)",
      "h3_list": ["Subsection point 1", "Subsection point 2"],
      "notes": "Key points and facts this section should cover (1-2 sentences)"
    }}
  ]
}}

Include 5-6 sections. The outline must be:
- SEO-friendly with natural keyword placement in H2/H3
- Logically structured: intro → body sections → conclusion
- Actionable and specific (not generic)"""

    text = _call_llm(prompt, provider, max_tokens=1500, json_mode=True)
    try:
        return json.loads(text)
    except Exception:
        return _extract_json_object(text)


# ---------------------------------------------------------------------------
# 3. Generate Full Blog from Outline
# ---------------------------------------------------------------------------

def generate_blog_from_outline(topic: str, outline: dict, model: str = MODEL_CLAUDE) -> dict:
    """Generate a complete, SEO-friendly blog post following the provided outline."""
    provider = _resolve_model(model, task='blog')

    sections_text = '\n'.join([
        f"## {s['h2']}\n"
        + '\n'.join([f"### {h}" for h in s.get('h3_list', [])])
        + (f"\n(Cover: {s['notes']})" if s.get('notes') else '')
        for s in outline.get('sections', [])
    ])

    keywords = ', '.join(outline.get('focus_keywords', []))

    prompt = f"""You are a talented magazine writer. Write a complete, engaging blog post based on this SEO outline.

Topic: {topic}
Title: {outline.get('title', topic)}
Focus Keywords: {keywords}
Target Word Count: {outline.get('word_count_target', 850)} words
Tone: {outline.get('tone', 'informative')}

OUTLINE TO FOLLOW:
{sections_text}

Requirements:
1. Follow the outline structure exactly — use the H2 and H3 headings as provided
2. Naturally weave the focus keywords throughout (don't stuff them)
3. Write an engaging hook in the introduction
4. Use concrete examples, data points, or actionable tips in each section
5. End with a strong conclusion
6. After the conclusion, add a "## Key Takeaways" section with 5-6 concise bullet points

Return ONLY a JSON object:
{{
  "title": "Final SEO article title",
  "excerpt": "2-sentence excerpt for SEO previews (includes primary keyword)",
  "content": "Full article in markdown with ## and ### headings",
  "summary_bullets": [
    "Key takeaway point 1",
    "Key takeaway point 2",
    "Key takeaway point 3",
    "Key takeaway point 4",
    "Key takeaway point 5"
  ]
}}"""

    text = _call_llm(prompt, provider, max_tokens=4096, json_mode=True)
    try:
        return json.loads(text)
    except Exception:
        return _extract_json_object(text)


# ---------------------------------------------------------------------------
# 4. Generate Blog Draft (legacy / direct — no outline step)
# ---------------------------------------------------------------------------

def generate_blog_draft(idea: str, model: str = MODEL_CLAUDE) -> dict:
    """Generate a full blog article draft directly from an idea. Kept for backward compatibility."""
    provider = _resolve_model(model, task='blog')

    prompt = f"""You are a talented magazine writer. Write a complete, engaging magazine article based on this idea:

"{idea}"

Write a well-structured article with:
1. A compelling headline/title
2. An engaging introduction that hooks the reader
3. Well-organised body sections (use ## for H2 subheadings, ### for H3)
4. Concrete examples and actionable advice
5. A strong conclusion
6. After the conclusion, a "## Key Takeaways" section with 5-6 bullet points
7. Target 700-900 words

Return ONLY a JSON object:
{{
  "title": "The Article Title",
  "excerpt": "A 1-2 sentence excerpt/teaser for the article",
  "content": "The full article content in markdown format",
  "summary_bullets": ["Key point 1", "Key point 2", "Key point 3", "Key point 4", "Key point 5"]
}}"""

    text = _call_llm(prompt, provider, max_tokens=4096, json_mode=True)
    try:
        return json.loads(text)
    except Exception:
        return _extract_json_object(text)


# ---------------------------------------------------------------------------
# 5. Trending Ideas (Admin Only)
# ---------------------------------------------------------------------------

def generate_trending_ideas(category: str = '', model: str = MODEL_CLAUDE) -> list:
    """Generate 10 currently trending article topics (used by admin only)."""
    provider = _resolve_model(model, task='ideas')
    cat_context = f'specifically for the "{category}" niche' if category else 'across all popular lifestyle, tech, culture, and society topics'

    prompt = f"""You are a digital trends analyst and senior magazine editor.

Generate 10 trending article topics {cat_context} that are popular RIGHT NOW and would drive high reader engagement.

Consider: viral social media topics, seasonal trends, evergreen high-search topics, emerging tech, cultural moments, health trends, and business insights.

Return ONLY a JSON array:
[
  {{
    "topic": "The trending topic or article title",
    "reason": "Why this is trending right now — be specific (1 sentence)",
    "search_volume": "High",
    "category": "lifestyle",
    "suggested_angle": "A unique, fresh angle to cover this topic",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }}
]

search_volume must be one of: "Very High", "High", "Medium"
category must be one of: lifestyle, technology, health, business, culture, travel, food, sports, environment, science"""

    text = _call_llm(prompt, provider, max_tokens=2000, json_mode=True)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        for key in ('topics', 'trending', 'ideas', 'results', 'items'):
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        return list(parsed.values())[0]
    except Exception:
        return _extract_json_list(text)


# ---------------------------------------------------------------------------
# 6. Generate Blog Image (DALL-E 3 via OpenAI)
# ---------------------------------------------------------------------------

def generate_blog_image(title: str, excerpt: str = '') -> str:
    """
    Generate a featured image for a blog post using DALL-E 3.
    Returns the image URL (expires in 1 hour — download and save immediately).
    """
    client = _get_openai()
    context = excerpt[:200] if excerpt else title

    image_prompt = (
        f"Create a high-quality, professional magazine cover photo for an article titled: '{title}'. "
        f"Context: {context}. "
        "Style: editorial photography, clean composition, vibrant but sophisticated colours, "
        "suitable for a premium digital magazine. No text or typography in the image."
    )

    response = client.images.generate(
        model='dall-e-3',
        prompt=image_prompt,
        size='1792x1024',
        quality='standard',
        n=1,
    )
    return response.data[0].url


def download_and_save_image(url: str, filename: str) -> bytes:
    """Download image from URL and return raw bytes."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content
