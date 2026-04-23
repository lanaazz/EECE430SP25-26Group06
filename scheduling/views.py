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

from .models import Match, TrainingSession, Team, Announcement, Payment, MatchStats, PlayerMatchStats, SessionAttendance
from .forms import MatchForm, TrainingSessionForm, MatchStatsForm, PlayerMatchStatsForm, AttendanceForm


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
            "url": f"/scheduling/match/{match.id}/" if hasattr(match, 'id') else "#",
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
            "url": f"/scheduling/training/{training.id}/" if hasattr(training, 'id') else "#",
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


@login_required
def match_detail(request, pk):
    """View match details including stats."""
    match = get_object_or_404(Match, pk=pk)
    
    # Check if user's team is involved in this match
    user_team = request.user.profile.team if hasattr(request.user, 'profile') else None
    if user_team and match.home_team != user_team and match.away_team != user_team:
        messages.error(request, "You can only view matches for your team.")
        return redirect('calendar')
    
    # Get match stats if available
    stats = getattr(match, 'stats', None)
    
    context = {
        'match': match,
        'stats': stats,
        'active_page': 'matches',
    }
    return render(request, 'scheduling/match_detail.html', context)


@login_required
def training_detail(request, pk):
    """View training session details."""
    training = get_object_or_404(TrainingSession, pk=pk)
    
    # Check if user's team is involved
    user_team = request.user.profile.team if hasattr(request.user, 'profile') else None
    if user_team and training.team != user_team:
        messages.error(request, "You can only view training sessions for your team.")
        return redirect('calendar')
    
    context = {
        'training': training,
        'active_page': 'training',
    }
    return render(request, 'scheduling/training_detail.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# SCRUM-15  Coach tracks detailed player statistics
# ─────────────────────────────────────────────────────────────────────────────

@coach_required
def player_match_stats(request, match_pk):
    """Coach views / edits per-player stats for a specific match."""
    match = get_object_or_404(Match, pk=match_pk)

    # Only matches for the coach's team
    user_team = request.user.profile.team
    if match.home_team != user_team and match.away_team != user_team:
        messages.error(request, "That match is not for your team.")
        return redirect('calendar')

    # Gather team players
    from django.contrib.auth.models import User as DjangoUser
    team_players = DjangoUser.objects.filter(
        profile__team=user_team,
        profile__role__in=['player', 'captain']
    ).order_by('username')

    if request.method == 'POST':
        # Bulk-save one row per player
        for player in team_players:
            strikes      = int(request.POST.get(f'strikes_{player.id}', 0) or 0)
            blocks       = int(request.POST.get(f'blocks_{player.id}', 0) or 0)
            service_aces = int(request.POST.get(f'aces_{player.id}', 0) or 0)
            errors       = int(request.POST.get(f'errors_{player.id}', 0) or 0)
            digs         = int(request.POST.get(f'digs_{player.id}', 0) or 0)
            assists      = int(request.POST.get(f'assists_{player.id}', 0) or 0)

            PlayerMatchStats.objects.update_or_create(
                match=match,
                player=player,
                defaults=dict(
                    strikes=strikes,
                    blocks=blocks,
                    service_aces=service_aces,
                    errors=errors,
                    digs=digs,
                    assists=assists,
                    recorded_by=request.user,
                )
            )
        messages.success(request, "Player statistics saved successfully.")
        return redirect('player_match_stats', match_pk=match_pk)

    # Prefill existing stats
    existing = {s.player_id: s for s in PlayerMatchStats.objects.filter(match=match)}
    player_rows = []
    for p in team_players:
        s = existing.get(p.id)
        player_rows.append({
            'player': p,
            'strikes':      s.strikes      if s else 0,
            'blocks':       s.blocks       if s else 0,
            'service_aces': s.service_aces if s else 0,
            'errors':       s.errors       if s else 0,
            'digs':         s.digs         if s else 0,
            'assists':      s.assists      if s else 0,
        })

    context = {
        'match': match,
        'player_rows': player_rows,
        'active_page': 'matches',
    }
    return render(request, 'scheduling/player_match_stats.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# SCRUM-17  View attendance trends
# ─────────────────────────────────────────────────────────────────────────────

@coach_required
def attendance_view(request, session_pk=None):
    """Coach records attendance for a training session and views trends."""
    from django.contrib.auth.models import User as DjangoUser

    user_team = request.user.profile.team

    # All sessions for this team, most-recent first
    sessions = TrainingSession.objects.filter(team=user_team).order_by('-date')

    selected_session = None
    player_rows = []

    if session_pk:
        selected_session = get_object_or_404(TrainingSession, pk=session_pk, team=user_team)

        team_players = DjangoUser.objects.filter(
            profile__team=user_team,
            profile__role__in=['player', 'captain']
        ).order_by('username')

        if request.method == 'POST':
            for player in team_players:
                status = request.POST.get(f'status_{player.id}', 'absent')
                SessionAttendance.objects.update_or_create(
                    session=selected_session,
                    player=player,
                    defaults={'status': status, 'recorded_by': request.user}
                )
            messages.success(request, "Attendance saved.")
            return redirect('attendance_view', session_pk=session_pk)

        existing = {a.player_id: a.status for a in SessionAttendance.objects.filter(session=selected_session)}
        for p in team_players:
            player_rows.append({'player': p, 'status': existing.get(p.id, 'absent')})

    # ── Attendance-trend data (last 10 sessions) ──────────────────────────
    recent_sessions = sessions[:10]
    trend_data = []
    for sess in recent_sessions:
        total   = SessionAttendance.objects.filter(session=sess).count()
        present = SessionAttendance.objects.filter(session=sess, status='present').count()
        trend_data.append({
            'label': sess.title[:20],
            'date':  sess.date.strftime('%d %b'),
            'total': total,
            'present': present,
            'rate': round(present / total * 100, 1) if total else 0,
        })

    context = {
        'sessions': sessions,
        'selected_session': selected_session,
        'player_rows': player_rows,
        'trend_data': json.dumps(list(reversed(trend_data))),
        'active_page': 'calendar',
    }
    return render(request, 'scheduling/attendance.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# SCRUM-25  Enter live match score  (coach)
# SCRUM-47  Player/Captain view current scores  (read-only live scoreboard)
# ─────────────────────────────────────────────────────────────────────────────

@coach_required
@require_POST
def start_live_match(request, pk):
    """Coach sets a match to 'live'."""
    match = get_object_or_404(Match, pk=pk)
    user_team = request.user.profile.team
    if match.home_team != user_team and match.away_team != user_team:
        messages.error(request, "Not your match.")
        return redirect('calendar')
    match.status = 'live'
    match.home_score = match.home_score or 0
    match.away_score = match.away_score or 0
    match.save()
    messages.success(request, "Match is now LIVE!")
    return redirect('live_score', pk=pk)


@coach_required
def update_live_score(request, pk):
    """Coach updates the live score."""
    match = get_object_or_404(Match, pk=pk)
    user_team = request.user.profile.team
    if match.home_team != user_team and match.away_team != user_team:
        messages.error(request, "Not your match.")
        return redirect('calendar')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'inc_home':
            match.home_score = (match.home_score or 0) + 1
        elif action == 'dec_home':
            match.home_score = max(0, (match.home_score or 0) - 1)
        elif action == 'inc_away':
            match.away_score = (match.away_score or 0) + 1
        elif action == 'dec_away':
            match.away_score = max(0, (match.away_score or 0) - 1)
        elif action == 'end_match':
            match.status = 'completed'
            match.save()
            messages.success(request, "Match ended and marked as completed.")
            return redirect('match_detail', pk=pk)
        match.save()
        # Return JSON for AJAX updates
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'home_score': match.home_score, 'away_score': match.away_score, 'status': match.status})
        return redirect('live_score', pk=pk)

    return redirect('live_score', pk=pk)


@login_required
def live_score(request, pk):
    """Live score view for coach (control) and players/captains (read-only)."""
    match = get_object_or_404(Match, pk=pk)
    user_team = request.user.profile.team if hasattr(request.user, 'profile') else None
    if user_team and match.home_team != user_team and match.away_team != user_team:
        messages.error(request, "You can only view matches for your team.")
        return redirect('matches')

    is_coach = hasattr(request.user, 'profile') and request.user.profile.role == 'coach'
    context = {
        'match': match,
        'is_coach': is_coach,
        'active_page': 'matches',
    }
    return render(request, 'scheduling/live_score.html', context)


@login_required
def live_score_api(request, pk):
    """JSON API returning current live score (SCRUM-27 polling endpoint)."""
    match = get_object_or_404(Match, pk=pk)
    return JsonResponse({
        'home_score': match.home_score or 0,
        'away_score': match.away_score or 0,
        'status': match.status,
        'home_team': match.home_team.name,
        'away_team': match.away_team.name,
    })


@login_required
def live_matches_api(request):
    """Returns all currently live matches for the user's team (SCRUM-27 dashboard sync)."""
    user_team = request.user.profile.team if hasattr(request.user, 'profile') else None
    if not user_team:
        return JsonResponse({'live_matches': []})

    from django.db.models import Q
    live = Match.objects.filter(
        status='live'
    ).filter(
        Q(home_team=user_team) | Q(away_team=user_team)
    ).select_related('home_team', 'away_team')

    data = [{
        'id': m.id,
        'home_team': m.home_team.name,
        'away_team': m.away_team.name,
        'home_score': m.home_score or 0,
        'away_score': m.away_score or 0,
        'url': f'/scheduling/match/{m.id}/live/',
    } for m in live]

    return JsonResponse({'live_matches': data})
