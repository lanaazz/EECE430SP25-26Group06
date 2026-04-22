from django.urls import path, include
from django.shortcuts import render
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from . import views

router = DefaultRouter(trailing_slash=True)
router.register(r'teams',         views.TeamViewSet,            basename='team')
router.register(r'matches',       views.MatchViewSet,           basename='match')
router.register(r'trainings',     views.TrainingSessionViewSet, basename='training')
router.register(r'announcements', views.AnnouncementViewSet,    basename='announcement')


ENDPOINT_GROUPS = [
    {
        'title': '🔐 Authentication',
        'endpoints': [
            ('POST', '/api/auth/register/', 'Register new user — returns token', False),
            ('POST', '/api/auth/login/',    'Login — returns token',             False),
            ('POST', '/api/auth/logout/',   'Logout — deletes token',            True),
            ('GET',  '/api/auth/me/',       'Get current user profile',          True),
            ('PUT',  '/api/auth/me/',       'Update current user profile',       True),
        ]
    },
    {
        'title': '📊 Dashboard',
        'endpoints': [
            ('GET', '/api/dashboard/', 'Upcoming events + announcements summary', True),
        ]
    },
    {
        'title': '🏐 Teams',
        'endpoints': [
            ('GET',    '/api/teams/',             'List all teams',        True),
            ('POST',   '/api/teams/',             'Create team (coach)',   True),
            ('GET',    '/api/teams/{id}/',         'Get team detail',       True),
            ('PUT',    '/api/teams/{id}/',         'Update team (coach)',   True),
            ('DELETE', '/api/teams/{id}/',         'Delete team (coach)',   True),
            ('GET',    '/api/teams/{id}/members/', 'List team members',    True),
        ]
    },
    {
        'title': '⚽ Matches',
        'endpoints': [
            ('GET',  '/api/matches/',             'List all matches',          True),
            ('POST', '/api/matches/',             'Create match (coach)',      True),
            ('GET',  '/api/matches/upcoming/',    'Upcoming matches only',     True),
            ('GET',  '/api/matches/{id}/',        'Get match detail',          True),
            ('PUT',  '/api/matches/{id}/',        'Update match (coach)',      True),
            ('POST', '/api/matches/{id}/cancel/', 'Cancel match (coach)',      True),
        ]
    },
    {
        'title': '🏋️ Training Sessions',
        'endpoints': [
            ('GET',  '/api/trainings/',              'List all sessions',         True),
            ('POST', '/api/trainings/',              'Create session (coach)',    True),
            ('GET',  '/api/trainings/upcoming/',     'Upcoming sessions only',   True),
            ('GET',  '/api/trainings/{id}/',         'Get session detail',        True),
            ('PUT',  '/api/trainings/{id}/',         'Update session (coach)',    True),
            ('POST', '/api/trainings/{id}/cancel/',  'Cancel session (coach)',    True),
        ]
    },
    {
        'title': '📢 Announcements',
        'endpoints': [
            ('GET',    '/api/announcements/',      'List announcements',          True),
            ('POST',   '/api/announcements/',      'Create announcement (coach)', True),
            ('GET',    '/api/announcements/{id}/', 'Get announcement detail',     True),
            ('PUT',    '/api/announcements/{id}/', 'Update announcement (coach)', True),
            ('DELETE', '/api/announcements/{id}/', 'Delete announcement (coach)', True),
        ]
    },
]


def api_root_view(request):
    """Custom themed API root page."""
    return render(request, 'rest_framework/api_root.html', {
        'groups': ENDPOINT_GROUPS,
        'user': request.user,
        'base_url': request.build_absolute_uri('/'),
    })


urlpatterns = [
    # Custom themed root
    path('', api_root_view, name='api_root'),

    # Auth endpoints
    path('auth/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('auth/login/',    views.LoginAPIView.as_view(),    name='api_login'),
    path('auth/logout/',   views.LogoutAPIView.as_view(),   name='api_logout'),
    path('auth/me/',       views.MeAPIView.as_view(),       name='api_me'),

    # Dashboard summary
    path('dashboard/', views.dashboard_summary, name='api_dashboard'),

    # ViewSet routes
    path('', include(router.urls)),
]
