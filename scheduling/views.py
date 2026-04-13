from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q
import json
import calendar
from datetime import datetime, date

from .models import Match, TrainingSession, Team, Announcement, Payment
from .forms import MatchForm, TrainingSessionForm


def coach_required(view_func):
    """Decorator to restrict views to coaches only."""
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'coach':
            messages.error(request, "Only coaches can access this page.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


import calendar
from django.shortcuts import render
from django.utils import timezone

# import your real models here
# from .models import Match, Training


def calendar_view(request):
    today = timezone.localdate()

    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    cal = calendar.Calendar(firstweekday=0)  # Monday
    month_matrix = cal.monthdayscalendar(year, month)

    month_name = calendar.month_name[month]
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Get user's team for filtering
    user_team = None
    is_coach = False
    if hasattr(request.user, 'profile'):
        user_team = request.user.profile.team
        is_coach = request.user.profile.role == 'coach'

    # ----------------------------
    # Filter by user's team
    # ----------------------------
    if user_team:
        upcoming_matches = Match.objects.filter(
            Q(home_team=user_team) | Q(away_team=user_team),
            date__year=year,
            date__month=month
        ).order_by("date")

        upcoming_trainings = TrainingSession.objects.filter(
            team=user_team,
            date__year=year,
            date__month=month
        ).order_by("date")
    else:
        upcoming_matches = []
        upcoming_trainings = []

    # Build events by day
    events_by_day = {}

    # Example for matches
    for match in upcoming_matches:
        day_num = match.date.day
        if day_num not in events_by_day:
            events_by_day[day_num] = []
        events_by_day[day_num].append({
            "type": "match",
            "status": getattr(match, "status", "scheduled"),
            "label": f"{match.home_team.name} vs {match.away_team.name}",
            "time": match.date.strftime("%H:%M"),
        })

    # Example for trainings
    for training in upcoming_trainings:
        day_num = training.date.day
        if day_num not in events_by_day:
            events_by_day[day_num] = []
        events_by_day[day_num].append({
            "type": "training",
            "status": getattr(training, "status", "scheduled"),
            "label": training.title,
            "time": training.date.strftime("%H:%M"),
        })

    # Flatten calendar into one list for template
    calendar_days = []
    for week in month_matrix:
        for day in week:
            if day == 0:
                calendar_days.append({
                    "day": "",
                    "is_empty": True,
                    "is_today": False,
                    "events": [],
                    "has_events": False,
                })
            else:
                day_events = events_by_day.get(day, [])
                calendar_days.append({
                    "day": day,
                    "is_empty": False,
                    "is_today": (
                        day == today.day and month == today.month and year == today.year
                    ),
                    "events": day_events,
                    "has_events": len(day_events) > 0,
                })

    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    context = {
        "today": today,
        "year": year,
        "month": month,
        "month_name": month_name,
        "weekdays": weekdays,
        "calendar_days": calendar_days,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "upcoming_matches": upcoming_matches[:5],
        "upcoming_trainings": upcoming_trainings[:5],
        "is_coach": is_coach,
    }

    return render(request, "scheduling/calendar.html", context)
@coach_required
def schedule_match(request):
    """Coach creates a new match."""
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            match = form.save(commit=False)
            match.created_by = request.user
            match.save()
            messages.success(request, f"Match scheduled: {match}")
            return redirect('calendar')
    else:
        form = MatchForm()

    context = {
        'form': form,
        'form_title': 'Schedule a Match',
        'active_page': 'calendar',
    }
    return render(request, 'scheduling/schedule_form.html', context)


@coach_required
def schedule_training(request):
    """Coach creates a new training session."""
    if request.method == 'POST':
        form = TrainingSessionForm(request.POST)
        if form.is_valid():
            training = form.save(commit=False)
            training.created_by = request.user
            training.save()
            messages.success(request, f"Training scheduled: {training.title}")
            return redirect('calendar')
    else:
        form = TrainingSessionForm()

    context = {
        'form': form,
        'form_title': 'Schedule a Training Session',
        'active_page': 'calendar',
    }
    return render(request, 'scheduling/schedule_form.html', context)


@coach_required
def edit_match(request, pk):
    """Coach edits an existing match."""
    match = get_object_or_404(Match, pk=pk)
    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, "Match updated successfully.")
            return redirect('calendar')
    else:
        form = MatchForm(instance=match)
        # Pre-fill datetime-local input
        if match.date:
            form.fields['date'].initial = match.date.strftime('%Y-%m-%dT%H:%M')

    context = {
        'form': form,
        'form_title': 'Edit Match',
        'edit_mode': True,
        'object': match,
        'active_page': 'calendar',
    }
    return render(request, 'scheduling/schedule_form.html', context)


@coach_required
def edit_training(request, pk):
    """Coach edits an existing training session."""
    training = get_object_or_404(TrainingSession, pk=pk)
    if request.method == 'POST':
        form = TrainingSessionForm(request.POST, instance=training)
        if form.is_valid():
            form.save()
            messages.success(request, "Training session updated.")
            return redirect('calendar')
    else:
        form = TrainingSessionForm(instance=training)
        if training.date:
            form.fields['date'].initial = training.date.strftime('%Y-%m-%dT%H:%M')

    context = {
        'form': form,
        'form_title': 'Edit Training Session',
        'edit_mode': True,
        'object': training,
        'active_page': 'calendar',
    }
    return render(request, 'scheduling/schedule_form.html', context)


@coach_required
@require_POST
def cancel_match(request, pk):
    """Coach cancels a match."""
    match = get_object_or_404(Match, pk=pk)
    match.status = 'cancelled'
    match.save()
    messages.success(request, f"Match '{match}' has been cancelled.")
    return redirect('calendar')


@coach_required
@require_POST
def cancel_training(request, pk):
    """Coach cancels a training session."""
    training = get_object_or_404(TrainingSession, pk=pk)
    training.status = 'cancelled'
    training.save()
    messages.success(request, f"Training '{training.title}' has been cancelled.")
    return redirect('calendar')


@login_required
def calendar_events_api(request):
    """JSON API for calendar events (used by frontend JS)."""
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))

    matches = Match.objects.filter(date__year=year, date__month=month).select_related('home_team', 'away_team')
    trainings = TrainingSession.objects.filter(date__year=year, date__month=month).select_related('team')

    events = []
    for m in matches:
        events.append({
            'id': m.id,
            'type': 'match',
            'title': f"{m.home_team.name} vs {m.away_team.name}",
            'date': m.date.strftime('%Y-%m-%d'),
            'time': m.date.strftime('%H:%M'),
            'location': m.location,
            'status': m.status,
        })
    for t in trainings:
        events.append({
            'id': t.id,
            'type': 'training',
            'title': t.title,
            'date': t.date.strftime('%Y-%m-%d'),
            'time': t.date.strftime('%H:%M'),
            'location': t.location,
            'status': t.status,
            'duration': t.duration_minutes,
        })

    return JsonResponse({'events': events})

@login_required
def team_win_rate(request):
    user = request.user

    if not hasattr(user, 'profile') or not user.profile.team:
        return render(request, 'scheduling/win_rate.html', {'error': 'No team assigned'})

    team = user.profile.team

    matches = Match.objects.filter(
        status='completed'
    ).filter(
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
        'team': team,
        'wins': wins,
        'total_matches': total_matches,
        'win_rate': round(win_rate, 2)
    }

    return render(request, 'scheduling/win_rate.html', context)

@login_required
def payment_status(request):
    """Display and manage payments for players, parents, and managers."""
    from django.contrib.auth.models import User
    
    allowed_roles = ['player', 'parent', 'manager']

    if not hasattr(request.user, 'profile') or request.user.profile.role not in allowed_roles:
        messages.error(request, "You are not authorized to access the payment page.")
        return redirect('dashboard')

    user_team = request.user.profile.team if hasattr(request.user, 'profile') else None

    # PLAYER VIEW - See only their payments
    if request.user.profile.role == 'player':
        payments = Payment.objects.filter(player=request.user).order_by('-due_date')
        context = {
            'payments': payments,
            'active_page': 'payments',
            'is_player': True,
            'is_parent_or_manager': False,
        }
        return render(request, 'scheduling/payment_status.html', context)
    
    # PARENT/MANAGER VIEW - Select a player and see/pay their payments
    else:
        selected_player_id = request.GET.get('player_id')
        selected_player = None
        payments = []

        # Get all players from the same team (if user has a team)
        available_players = []
        if user_team:
            available_players = User.objects.filter(
                profile__team=user_team,
                profile__role='player'
            ).select_related('profile').order_by('username')

        # Process payment form submission
        if request.method == 'POST' and selected_player_id:
            try:
                selected_player = User.objects.get(id=selected_player_id)
                # Verify player is from same team
                if selected_player.profile.team != user_team:
                    messages.error(request, "Cannot access this player's payments.")
                    return redirect('payment_status')
                
                payment_id = request.POST.get('payment_id')
                try:
                    payment = Payment.objects.get(id=payment_id, player=selected_player)
                    # Mark as paid (demo)
                    payment.status = 'paid'
                    payment.paid_date = timezone.now().date()
                    payment.save()
                    messages.success(request, f"Payment of ${payment.amount} marked as paid (Demo)!")
                    return redirect(f'payment_status?player_id={selected_player_id}')
                except Payment.DoesNotExist:
                    messages.error(request, "Payment not found.")
            except User.DoesNotExist:
                messages.error(request, "Player not found.")
                return redirect('payment_status')

        # Load selected player's payments
        if selected_player_id:
            try:
                selected_player = User.objects.get(id=selected_player_id)
                if selected_player.profile.team != user_team:
                    messages.error(request, "Cannot access this player's payments.")
                    return redirect('payment_status')
                payments = Payment.objects.filter(player=selected_player).order_by('-due_date')
            except User.DoesNotExist:
                pass

        context = {
            'payments': payments,
            'active_page': 'payments',
            'is_player': False,
            'is_parent_or_manager': True,
            'available_players': available_players,
            'selected_player': selected_player,
            'selected_player_id': selected_player_id,
        }
        return render(request, 'scheduling/payment_status.html', context)
