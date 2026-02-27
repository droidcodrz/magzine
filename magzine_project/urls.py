from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = 'Magzine Admin'
admin.site.site_title = 'Magzine'
admin.site.index_title = 'Magazine Management'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('articles.urls')),
    path('accounts/', include('accounts.urls')),
    path('ai/', include('ai_tools.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
