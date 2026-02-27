from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import re
from .models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-control'}),
    )
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('Username may only contain letters, digits and @/./+/-/_ characters.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email.lower()


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-control', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}),
    )


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'bio', 'avatar')

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 2 * 1024 * 1024:
                raise ValidationError('Image file too large. Maximum size is 2MB.')
            if not avatar.content_type.startswith('image/'):
                raise ValidationError('Only image files are allowed.')
        return avatar
