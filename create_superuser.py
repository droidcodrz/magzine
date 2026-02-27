"""
Script to create superuser and sample data.
Run with: python manage.py shell < create_superuser.py
Or: python create_superuser.py (from project root)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'magzine_project.settings')
django.setup()

from accounts.models import User
from articles.models import Category

# Create superuser
if not User.objects.filter(email='admin@magzine.com').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@magzine.com',
        password='Admin@12345',
        first_name='Admin',
        last_name='User',
        role='editor',
    )
    print(f'Superuser created: {admin.email} / Admin@12345')
else:
    print('Superuser already exists.')

# Create default categories
categories = [
    ('People', 'bi-person-fill'),
    ('Events', 'bi-calendar-event-fill'),
    ('Places', 'bi-geo-alt-fill'),
    ('Culture', 'bi-palette-fill'),
    ('Technology', 'bi-cpu-fill'),
    ('Lifestyle', 'bi-heart-fill'),
    ('Business', 'bi-briefcase-fill'),
    ('Travel', 'bi-airplane-fill'),
    ('Health', 'bi-heart-pulse-fill'),
    ('Arts', 'bi-music-note-beamed'),
]

for name, icon in categories:
    cat, created = Category.objects.get_or_create(name=name, defaults={'icon': icon})
    if created:
        print(f'Category created: {name}')

print('\nSetup complete!')
print('Login at: http://localhost:8000/accounts/login/')
print('Admin at: http://localhost:8000/admin/')
print('Credentials: admin@magzine.com / Admin@12345')
