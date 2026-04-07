from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views as project_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication (SCRUM-28)
    path('', include('accounts.urls')),

    # App pages
    path('',              project_views.dashboard,      name='dashboard'),
    path('dashboard/',    project_views.dashboard,      name='dashboard'),
    path('matches/',      project_views.matches,        name='matches'),
    path('statistics/',   project_views.statistics,     name='statistics'),
    path('messages/',     project_views.messages_view,  name='messages'),
    path('news/',         project_views.news,           name='news'),
    path('achievements/', project_views.achievements,   name='achievements'),
    path('notifications/',project_views.notifications,  name='notifications'),

    # Scheduling (SCRUM-12)
    path('', include('scheduling.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
