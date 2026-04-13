from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from scheduling.models import Match, TrainingSession, Announcement, Team, UserProfile, Achievement, PlayerAchievement, News, Payment
from messaging.models import Notification
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import datetime


@login_required
def dashboard(request):
    today = timezone.now()
    upcoming_events = []

    # Get user's team
    user_team = None
    if hasattr(request.user, 'profile') and request.user.profile.team:
        user_team = request.user.profile.team

    # Filter by user's team only
    if user_team:
        upcoming_matches = Match.objects.filter(
            Q(home_team=user_team) | Q(away_team=user_team),
            date__gte=today, 
            status='upcoming'
        ).select_related('home_team', 'away_team').order_by('date')[:3]

        upcoming_trainings = TrainingSession.objects.filter(
            team=user_team,
            date__gte=today, 
            status='scheduled'
        ).select_related('team').order_by('date')[:3]
    else:
        upcoming_matches = []
        upcoming_trainings = []

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
    
    # Get user's team
    user_team = None
    if hasattr(request.user, 'profile') and request.user.profile.team:
        user_team = request.user.profile.team

    # Filter by user's team only
    if user_team:
        upcoming = Match.objects.filter(
            Q(home_team=user_team) | Q(away_team=user_team),
            date__gte=today, 
            status='upcoming'
        ).select_related('home_team', 'away_team').order_by('date')
        
        past = Match.objects.filter(
            Q(home_team=user_team) | Q(away_team=user_team),
            status='completed'
        ).select_related('home_team', 'away_team').order_by('-date')[:10]
    else:
        upcoming = []
        past = []

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
        losses = 0
        match_data = []
    else:
        team = user.profile.team

        matches = Match.objects.filter(status='completed').filter(
            Q(home_team=team) | Q(away_team=team)
        ).select_related('home_team', 'away_team').order_by('date')

        total_matches = matches.count()
        wins = 0
        losses = 0
        match_data = []

        for match in matches:
            if match.home_team == team:
                if match.home_score > match.away_score:
                    wins += 1
                    result = 'W'
                else:
                    losses += 1
                    result = 'L'
                score_display = f"{match.home_score}-{match.away_score}"
                opponent = match.away_team.name
            else:  # away team
                if match.away_score > match.home_score:
                    wins += 1
                    result = 'W'
                else:
                    losses += 1
                    result = 'L'
                score_display = f"{match.away_score}-{match.home_score}"
                opponent = match.home_team.name

            match_data.append({
                'date': match.date.strftime("%b %d, %Y"),
                'opponent': opponent,
                'score': score_display,
                'result': result,
            })

        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0

    context = {
        'active_page': 'statistics',
        'win_rate': round(win_rate, 2),
        'wins': wins,
        'losses': wins and total_matches - wins or 0,
        'total_matches': total_matches,
        'match_data': match_data,
    }

    return render(request, 'statistics.html', context)


@login_required
def messages_view(request):
    context = {'active_page': 'messages'}
    return render(request, 'messages.html', context)


@login_required
def news(request):
    """Display and manage team news/links."""
    user = request.user
    is_coach = hasattr(user, 'profile') and user.profile.role in ['coach', 'captain']
    
    user_team = None
    if hasattr(user, 'profile') and user.profile.team:
        user_team = user.profile.team
    
    if not user_team:
        return render(request, 'news.html', {
            'active_page': 'news',
            'news_list': [],
            'is_coach': is_coach,
        })

    # Handle form submission for coaches
    if request.method == 'POST' and is_coach:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        url = request.POST.get('url', '').strip()
        
        if title and url:
            News.objects.create(
                team=user_team,
                title=title,
                description=description,
                url=url,
                created_by=user
            )
            messages.success(request, "News link added successfully!")
            return redirect('news')
        else:
            messages.error(request, "Title and URL are required.")

    # Get team news
    news_list = News.objects.filter(team=user_team).order_by('-created_at')

    context = {
        'active_page': 'news',
        'news_list': news_list,
        'is_coach': is_coach,
    }
    return render(request, 'news.html', context)


@login_required
def achievements(request):
    """View for managing/viewing team achievements and player awards."""
    user = request.user
    
    if not hasattr(user, 'profile'):
        messages.error(request, "You must have a user profile.")
        return redirect('dashboard')
    
    user_team = user.profile.team
    if not user_team:
        messages.error(request, "You must be assigned to a team.")
        return redirect('dashboard')

    is_coach = user.profile.role in ['coach', 'captain']
    
    # COACH/CAPTAIN VIEW - Full management
    if is_coach:
        # Get selected player (if any)
        selected_player_id = request.GET.get('player_id')
        selected_player = None
        player_achievements = []
        available_achievements = []

        if selected_player_id:
            try:
                selected_player = UserProfile.objects.get(
                    pk=selected_player_id, 
                    team=user_team,
                    role__in=['player', 'captain']
                ).user
                # Get player's current achievements
                player_achievements = PlayerAchievement.objects.filter(
                    player=selected_player
                ).select_related('achievement', 'awarded_by').order_by('-awarded_at')
                
                # Get available achievements for quick assignment
                available_achievements = Achievement.objects.filter(
                    team=user_team
                ).exclude(
                    id__in=PlayerAchievement.objects.filter(
                        player=selected_player
                    ).values_list('achievement_id', flat=True)
                )
            except UserProfile.DoesNotExist:
                selected_player = None

        # Get all team members (players and captains)
        team_members = UserProfile.objects.filter(
            team=user_team,
            role__in=['player', 'captain']
        ).select_related('user')

        # Get all team achievements
        team_achievements = Achievement.objects.filter(team=user_team).order_by('name')

        context = {
            'active_page': 'achievements',
            'is_coach': is_coach,
            'user_team': user_team,
            'team_members': team_members,
            'team_achievements': team_achievements,
            'selected_player': selected_player,
            'selected_player_id': selected_player_id,
            'player_achievements': player_achievements,
            'available_achievements': available_achievements,
        }
        return render(request, 'achievements.html', context)
    
    # PLAYER VIEW - Read-only achievements display
    else:
        player_achievements = PlayerAchievement.objects.filter(
            player=user
        ).select_related('achievement', 'awarded_by').order_by('-awarded_at')
        
        team_achievements = Achievement.objects.filter(team=user_team)

        context = {
            'active_page': 'achievements',
            'is_coach': is_coach,
            'user_team': user_team,
            'player_achievements': player_achievements,
            'team_achievements': team_achievements,
        }
        return render(request, 'achievements.html', context)


@login_required
@require_POST
def add_achievement(request):
    """Coach adds a new achievement to the team."""
    user = request.user
    
    if not hasattr(user, 'profile') or user.profile.role not in ['coach', 'captain']:
        messages.error(request, "Unauthorized")
        return redirect('dashboard')
    
    user_team = user.profile.team
    if not user_team:
        messages.error(request, "No team assigned")
        return redirect('dashboard')

    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    icon = request.POST.get('icon', '🏆').strip()

    if not name:
        messages.error(request, "Achievement name is required")
        return redirect('achievements')

    achievement, created = Achievement.objects.get_or_create(
        team=user_team,
        name=name,
        defaults={'description': description, 'icon': icon}
    )

    if created:
        messages.success(request, f"Achievement '{name}' created successfully!")
    else:
        achievement.description = description
        achievement.icon = icon
        achievement.save()
        messages.info(request, f"Achievement '{name}' updated")

    return redirect('achievements')


@login_required
@require_POST
def award_achievement(request):
    """Coach awards an achievement to a player."""
    user = request.user
    
    if not hasattr(user, 'profile') or user.profile.role not in ['coach', 'captain']:
        messages.error(request, "Unauthorized")
        return redirect('dashboard')
    
    user_team = user.profile.team
    if not user_team:
        messages.error(request, "No team assigned")
        return redirect('dashboard')

    player_id = request.POST.get('player_id')
    achievement_id = request.POST.get('achievement_id')
    notes = request.POST.get('notes', '').strip()

    try:
        player = UserProfile.objects.get(pk=player_id, team=user_team).user
        achievement = Achievement.objects.get(pk=achievement_id, team=user_team)
    except (UserProfile.DoesNotExist, Achievement.DoesNotExist):
        messages.error(request, "Invalid player or achievement")
        return redirect('achievements')

    # Create or update the award
    award, created = PlayerAchievement.objects.get_or_create(
        player=player,
        achievement=achievement,
        defaults={'awarded_by': user, 'notes': notes}
    )

    if not created:
        award.notes = notes
        award.awarded_by = user
        award.awarded_at = timezone.now()
        award.save()
        messages.info(request, f"Award updated for {player.username}")
    else:
        messages.success(request, f"Achievement awarded to {player.username}!")

    return redirect(f'achievements?player_id={player_id}')


@login_required
@require_POST
def remove_achievement(request):
    """Coach removes an achievement from a player."""
    user = request.user
    
    if not hasattr(user, 'profile') or user.profile.role not in ['coach', 'captain']:
        messages.error(request, "Unauthorized")
        return redirect('dashboard')

    award_id = request.POST.get('award_id')

    try:
        award = PlayerAchievement.objects.get(pk=award_id)
        # Verify the achievement belongs to user's team
        if award.achievement.team != user.profile.team:
            messages.error(request, "Unauthorized")
            return redirect('achievements')
        
        player_id = award.player.profile.id
        award.delete()
        messages.success(request, "Achievement removed!")
        return redirect(f'achievements?player_id={player_id}')
    except PlayerAchievement.DoesNotExist:
        messages.error(request, "Award not found")
        return redirect('achievements')


@login_required
def notifications(request):
    """Display user's notifications."""
    user = request.user
    
    # Get user's notifications, mark as read if viewing detail
    user_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:50]
    
    context = {
        'active_page': 'notifications',
        'notifications': user_notifications,
    }
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
