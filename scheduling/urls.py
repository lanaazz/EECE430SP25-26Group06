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
    path('payments/report/', views.payment_report, name='payment_report'),
    
    # Match scheduling (coach only)
    path('schedule/match/', views.schedule_match, name='schedule_match'),
    path('schedule/match/<int:pk>/edit/', views.edit_match, name='edit_match'),
    path('schedule/match/<int:pk>/cancel/', views.cancel_match, name='cancel_match'),

    # Training scheduling (coach only)
    path('schedule/training/', views.schedule_training, name='schedule_training'),
    path('schedule/training/<int:pk>/edit/', views.edit_training, name='edit_training'),
    path('schedule/training/<int:pk>/cancel/', views.cancel_training, name='cancel_training'),

    # SCRUM-15: Coach tracks detailed player statistics
    path('match/<int:match_pk>/player-stats/', views.player_match_stats, name='player_match_stats'),

    # SCRUM-17: View attendance trends
    path('attendance/', views.attendance_view, name='attendance_view'),
    path('attendance/<int:session_pk>/', views.attendance_view, name='attendance_view'),

    # SCRUM-25: Enter live match score (coach)
    # SCRUM-47: Player/Captain view current scores
    path('match/<int:pk>/live/', views.live_score, name='live_score'),
    path('match/<int:pk>/start-live/', views.start_live_match, name='start_live_match'),
    path('match/<int:pk>/update-score/', views.update_live_score, name='update_live_score'),

    # SCRUM-27: Live score JSON API (for dashboard sync)
    path('match/<int:pk>/score-api/', views.live_score_api, name='live_score_api'),
    path('live-matches/', views.live_matches_api, name='live_matches_api'),
]
