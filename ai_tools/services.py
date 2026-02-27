import json
import re
import anthropic
import openai as openai_lib
from django.conf import settings


# ---------------------------------------------------------------------------
# Model constants
# ---------------------------------------------------------------------------
MODEL_CLAUDE = 'claude'
MODEL_OPENAI = 'openai'
MODEL_AUTO   = 'auto'

CLAUDE_MODEL  = 'claude-sonnet-4-6'
OPENAI_MODEL  = 'gpt-4o'

# Auto-routing: use Claude for creative/blog writing, OpenAI for research/ideas
AUTO_BLOG_MODEL  = MODEL_CLAUDE
AUTO_IDEAS_MODEL = MODEL_OPENAI  # Falls back to Claude if no OpenAI key


def _resolve_model(selected: str, task: str) -> str:
    """
    Resolve 'auto' to an actual provider based on task type and available keys.
    task: 'blog' or 'ideas'
    Returns: 'claude' or 'openai'
    """
    if selected == MODEL_AUTO:
        preferred = AUTO_BLOG_MODEL if task == 'blog' else AUTO_IDEAS_MODEL
        # Fall back to Claude if OpenAI key not available
        if preferred == MODEL_OPENAI and not settings.OPENAI_API_KEY:
            return MODEL_CLAUDE
        if preferred == MODEL_CLAUDE and not settings.ANTHROPIC_API_KEY:
            return MODEL_OPENAI
        return preferred
    return selected


def _get_anthropic():
    key = settings.ANTHROPIC_API_KEY
    if not key:
        raise ValueError('ANTHROPIC_API_KEY is not configured. Please set it in your .env file.')
    return anthropic.Anthropic(api_key=key)


def _get_openai():
    key = settings.OPENAI_API_KEY
    if not key:
        raise ValueError('OPENAI_API_KEY is not configured. Please set it in your .env file.')
    return openai_lib.OpenAI(api_key=key)


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


# ---------------------------------------------------------------------------
# Generate Article Ideas
# ---------------------------------------------------------------------------

def generate_article_ideas(topics: list, additional_context: str = '', model: str = MODEL_CLAUDE) -> list:
    """Generate magazine article ideas. Supports claude, openai, and auto."""
    provider = _resolve_model(model, task='ideas')
    topics_str = ', '.join(topics)
    context_str = f'\nAdditional focus: {additional_context}' if additional_context else ''

    prompt = f"""You are a creative magazine editor for a modern, sophisticated magazine.
Generate 8 compelling, original magazine article ideas based on these topic categories: {topics_str}.{context_str}

For each idea, provide:
1. A catchy, engaging title
2. A 2-3 sentence description of the article
3. The main angle or hook
4. Target audience

Format your response as a JSON array ONLY (no extra text):
[
  {{
    "title": "Article Title Here",
    "description": "2-3 sentence description",
    "angle": "The unique hook or angle",
    "audience": "Target reader description"
  }}
]

Make the ideas diverse, timely, and genuinely interesting."""

    if provider == MODEL_OPENAI:
        client = _get_openai()
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=2048,
            response_format={'type': 'json_object'},
        )
        text = response.choices[0].message.content
        # OpenAI with json_object wraps in an object, so try both
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            # Common wrapper keys
            for key in ('ideas', 'articles', 'results', 'items'):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
            return list(parsed.values())[0]
        except Exception:
            return _extract_json_list(text)
    else:
        client = _get_anthropic()
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return _extract_json_list(message.content[0].text)


# ---------------------------------------------------------------------------
# Generate Blog Draft
# ---------------------------------------------------------------------------

def generate_blog_draft(idea: str, model: str = MODEL_CLAUDE) -> dict:
    """Generate a full blog article draft. Supports claude, openai, and auto."""
    provider = _resolve_model(model, task='blog')

    prompt = f"""You are a talented magazine writer. Write a complete, engaging magazine article based on this idea:

"{idea}"

Write a well-structured article with:
1. A compelling headline/title
2. An engaging introduction that hooks the reader
3. Well-organized body with clear sections (use ## for subheadings)
4. Quotes or examples where appropriate
5. A strong conclusion
6. The article should be 600-900 words

Respond with a JSON object ONLY (no extra text):
{{
  "title": "The Article Title",
  "excerpt": "A 1-2 sentence excerpt/teaser for the article",
  "content": "The full article content in markdown format"
}}

Make it sophisticated, well-researched in tone, and appropriate for a premium magazine audience."""

    if provider == MODEL_OPENAI:
        client = _get_openai()
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=4096,
            response_format={'type': 'json_object'},
        )
        text = response.choices[0].message.content
        try:
            return json.loads(text)
        except Exception:
            return _extract_json_object(text)
    else:
        client = _get_anthropic()
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return _extract_json_object(message.content[0].text)
