from django import forms
from django.core.exceptions import ValidationError
from .models import Article, Comment, Category, Tag


class ArticleForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Add tags separated by commas (e.g. travel, lifestyle, culture)',
        }),
        label='Tags',
    )
    title = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Article title'}),
    )
    excerpt = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short summary of the article'}),
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control article-editor', 'rows': 20}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='Select Category',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status = forms.ChoiceField(
        choices=Article.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    cover_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )
    is_featured = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = Article
        fields = ('title', 'category', 'cover_image', 'excerpt', 'content', 'status', 'is_featured')

    def clean_cover_image(self):
        cover_image = self.cleaned_data.get('cover_image')
        if cover_image and hasattr(cover_image, 'size'):
            if cover_image.size > 5 * 1024 * 1024:
                raise ValidationError('Image too large. Maximum size is 5MB.')
            if not cover_image.content_type.startswith('image/'):
                raise ValidationError('Only image files are allowed.')
        return cover_image

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise ValidationError('Title must be at least 5 characters long.')
        return title

    def save(self, commit=True):
        article = super().save(commit=False)
        if commit:
            article.save()
            # Handle tags
            tags_input = self.cleaned_data.get('tags_input', '')
            article.tags.clear()
            if tags_input:
                for tag_name in tags_input.split(','):
                    tag_name = tag_name.strip().lower()
                    if tag_name:
                        tag, _ = Tag.objects.get_or_create(name=tag_name)
                        article.tags.add(tag)
        return article


class CommentForm(forms.ModelForm):
    content = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your thoughts...',
        }),
        label='',
    )

    class Meta:
        model = Comment
        fields = ('content',)

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 5:
            raise ValidationError('Comment is too short.')
        return content
