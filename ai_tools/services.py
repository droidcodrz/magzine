import anthropic
from django.conf import settings


def get_client():
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError('ANTHROPIC_API_KEY is not configured. Please set it in your .env file.')
    return anthropic.Anthropic(api_key=api_key)


def generate_article_ideas(topics: list, additional_context: str = '') -> list:
    """Generate magazine article ideas based on selected topics."""
    client = get_client()

    topics_str = ', '.join(topics)
    context_str = f'\nAdditional focus: {additional_context}' if additional_context else ''

    prompt = f"""You are a creative magazine editor for a modern, sophisticated magazine.
Generate 8 compelling, original magazine article ideas based on these topic categories: {topics_str}.{context_str}

For each idea, provide:
1. A catchy, engaging title
2. A 2-3 sentence description of the article
3. The main angle or hook
4. Target audience

Format your response as a JSON array with this structure:
[
  {{
    "title": "Article Title Here",
    "description": "2-3 sentence description",
    "angle": "The unique hook or angle",
    "audience": "Target reader description"
  }}
]

Make the ideas diverse, timely, and genuinely interesting. Focus on stories that would captivate readers."""

    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=2048,
        messages=[{'role': 'user', 'content': prompt}],
    )

    import json
    import re
    response_text = message.content[0].text

    # Extract JSON from response
    json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if json_match:
        ideas = json.loads(json_match.group())
    else:
        ideas = json.loads(response_text)

    return ideas


def generate_blog_draft(idea: str) -> dict:
    """Generate a full blog article draft from an idea."""
    client = get_client()

    prompt = f"""You are a talented magazine writer. Write a complete, engaging magazine article based on this idea:

"{idea}"

Write a well-structured article with:
1. A compelling headline/title
2. An engaging introduction that hooks the reader
3. Well-organized body with clear sections (use ## for subheadings)
4. Quotes or examples where appropriate
5. A strong conclusion
6. The article should be 600-900 words

Format your response as JSON:
{{
  "title": "The Article Title",
  "excerpt": "A 1-2 sentence excerpt/teaser for the article",
  "content": "The full article content in markdown format"
}}

Make it sophisticated, well-researched in tone, and appropriate for a premium magazine audience."""

    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=4096,
        messages=[{'role': 'user', 'content': prompt}],
    )

    import json
    import re
    response_text = message.content[0].text

    # Extract JSON from response
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group())
    else:
        result = json.loads(response_text)

    return result
