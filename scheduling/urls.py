from django.urls import path
from . import views

urlpatterns = [
    # Calendar
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/api/events/', views.calendar_events_api, name='calendar_events_api'),

    # Match details (view)
    path('match/<int:pk>/', views.match_detail, name='match_detail'),
    
    # Training details (view)
    path('training/<int:pk>/', views.training_detail, name='training_detail'),

    path('win-rate/', views.team_win_rate, name='team_win_rate'),
    path('payments/', views.payment_status, name='payment_status'),
    
    # Match scheduling (coach only)
    path('schedule/match/', views.schedule_match, name='schedule_match'),
    path('schedule/match/<int:pk>/edit/', views.edit_match, name='edit_match'),
    path('schedule/match/<int:pk>/cancel/', views.cancel_match, name='cancel_match'),

    # Training scheduling (coach only)
    path('schedule/training/', views.schedule_training, name='schedule_training'),
    path('schedule/training/<int:pk>/edit/', views.edit_training, name='edit_training'),
    path('schedule/training/<int:pk>/cancel/', views.cancel_training, name='cancel_training'),
]
