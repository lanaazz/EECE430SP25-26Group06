from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from scheduling.models import Match, TrainingSession, Announcement

@login_required
def dashboard(request):
    today = timezone.now()
    upcoming_events = []

    # Combine upcoming matches and trainings for dashboard
    upcoming_matches = Match.objects.filter(
        date__gte=today, status='upcoming'
    ).select_related('home_team', 'away_team').order_by('date')[:3]

    upcoming_trainings = TrainingSession.objects.filter(
        date__gte=today, status='scheduled'
    ).select_related('team').order_by('date')[:3]

    announcements = []
    if hasattr(request.user, 'profile') and request.user.profile.team:
        announcements = Announcement.objects.filter(
            team=request.user.profile.team
        ).order_by('-created_at')[:3]

    context = {
        'upcoming_matches': upcoming_matches,
        'upcoming_trainings': upcoming_trainings,
        'announcements': announcements,
        'active_page': 'dashboard',
    }
    return render(request, 'dashboard.html', context)


@login_required
def matches(request):
    today = timezone.now()
    upcoming = Match.objects.filter(date__gte=today, status='upcoming').select_related(
        'home_team', 'away_team').order_by('date')
    past = Match.objects.filter(status='completed').select_related(
        'home_team', 'away_team').order_by('-date')[:10]

    context = {
        'upcoming_matches': upcoming,
        'past_matches': past,
        'active_page': 'matches',
    }
    return render(request, 'matches.html', context)

@login_required
def statistics(request):
    user = request.user

    if not hasattr(user, 'profile') or not user.profile.team:
        win_rate = 0
        wins = 0
        total_matches = 0
    else:
        team = user.profile.team

        matches = Match.objects.filter(status='completed').filter(
            home_team=team
        ) | Match.objects.filter(
            status='completed',
            away_team=team
        )

        total_matches = matches.count()
        wins = 0

        for match in matches:
            if match.home_team == team and match.home_score > match.away_score:
                wins += 1
            elif match.away_team == team and match.away_score > match.home_score:
                wins += 1

        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0

    context = {
        'active_page': 'statistics',
        'win_rate': round(win_rate, 2),
    }

    return render(request, 'statistics.html', context)

@login_required
def messages_view(request):
    context = {'active_page': 'messages'}
    return render(request, 'messages.html', context)


@login_required
def news(request):
    context = {'active_page': 'news'}
    return render(request, 'news.html', context)


@login_required
def achievements(request):
    context = {'active_page': 'achievements'}
    return render(request, 'achievements.html', context)


@login_required
def notifications(request):
    context = {'active_page': 'notifications'}
    return render(request, 'notifications.html', context)


def role_select(request):
    """Role selection screen shown after login."""
    if request.method == 'POST':
        role = request.POST.get('role')
        if role and hasattr(request.user, 'profile'):
            request.user.profile.role = role
            request.user.profile.save()
        return redirect('dashboard')
    return render(request, 'auth/role_select.html', {'active_page': ''})
