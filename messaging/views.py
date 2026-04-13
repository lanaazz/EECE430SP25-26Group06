from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Conversation, Message, Notification
from scheduling.models import UserProfile


@login_required
def inbox(request):
    """Main messaging inbox — lists all conversations."""
    conversations = request.user.conversations.prefetch_related(
        'participants', 'messages'
    ).order_by('-created_at')

    # Annotate unread counts
    conv_data = []
    for conv in conversations:
        last_msg = conv.last_message()
        unread = conv.unread_count(request.user)
        other_participants = conv.participants.exclude(id=request.user.id)
        conv_data.append({
            'conv': conv,
            'last_msg': last_msg,
            'unread': unread,
            'others': other_participants,
        })

    # Filter users based on role
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    user_team = user_profile.team if user_profile else None
    user_role = user_profile.role if user_profile else None
    
    if user_role in ['coach', 'manager']:
        # Coaches and managers can message anyone
        all_users = User.objects.exclude(id=request.user.id).select_related('profile')
    else:
        # Players, parents, captains can only message their team members
        if user_team:
            all_users = User.objects.filter(
                profile__team=user_team
            ).exclude(id=request.user.id).select_related('profile')
        else:
            all_users = User.objects.none()

    context = {
        'conv_data': conv_data,
        'all_users': all_users,
        'active_page': 'messages',
    }
    return render(request, 'messaging/inbox.html', context)


@login_required
def conversation_detail(request, conv_id):
    """View and reply in a conversation."""
    conv = get_object_or_404(Conversation, id=conv_id)

    # Must be a participant
    if request.user not in conv.participants.all():
        django_messages.error(request, "You are not part of this conversation.")
        return redirect('inbox')

    # Mark all messages as read
    for msg in conv.messages.exclude(read_by=request.user).exclude(sender=request.user):
        msg.mark_read(request.user)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            msg = Message.objects.create(
                conversation=conv,
                sender=request.user,
                body=body,
            )
            # Notify other participants
            for participant in conv.participants.exclude(id=request.user.id):
                Notification.objects.create(
                    user=participant,
                    type='message',
                    title=f"New message from {request.user.username}",
                    body=body[:100],
                    link=f"/messages/{conv.id}/",
                )
        return redirect('conversation_detail', conv_id=conv.id)

    msgs = conv.messages.select_related('sender').prefetch_related('read_by')
    other_participants = conv.participants.exclude(id=request.user.id)

    # All conversations for sidebar
    all_convs = request.user.conversations.prefetch_related('participants', 'messages')
    conv_data = []
    for c in all_convs:
        conv_data.append({
            'conv': c,
            'last_msg': c.last_message(),
            'unread': c.unread_count(request.user),
            'others': c.participants.exclude(id=request.user.id),
        })

    context = {
        'conv': conv,
        'msgs': msgs,
        'other_participants': other_participants,
        'conv_data': conv_data,
        'active_page': 'messages',
    }
    return render(request, 'messaging/conversation.html', context)


@login_required
def start_direct_message(request, user_id):
    """Start or open a DM with another user."""
    other_user = get_object_or_404(User, id=user_id)

    if other_user == request.user:
        return redirect('inbox')

    # Check permissions: can current user message other_user?
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    other_profile = other_user.profile if hasattr(other_user, 'profile') else None
    user_role = user_profile.role if user_profile else None
    user_team = user_profile.team if user_profile else None
    other_team = other_profile.team if other_profile else None
    
    # Coaches and managers can message anyone
    if user_role not in ['coach', 'manager']:
        # Players, parents, captains can only message their team members
        if not user_team or user_team != other_team:
            django_messages.error(request, "You can only message members of your team.")
            return redirect('inbox')

    # Check if DM already exists
    existing = Conversation.objects.filter(
        type='direct',
        participants=request.user
    ).filter(participants=other_user)

    if existing.exists():
        return redirect('conversation_detail', conv_id=existing.first().id)

    # Create new DM
    conv = Conversation.objects.create(
        type='direct',
        created_by=request.user,
    )
    conv.participants.add(request.user, other_user)
    return redirect('conversation_detail', conv_id=conv.id)


@login_required
def create_group_chat(request):
    """Coach or captain creates a group chat."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        participant_ids = request.POST.getlist('participants')

        if not name:
            django_messages.error(request, "Group name is required.")
            return redirect('inbox')

        conv = Conversation.objects.create(
            type='group',
            name=name,
            created_by=request.user,
        )
        conv.participants.add(request.user)
        for uid in participant_ids:
            try:
                user = User.objects.get(id=uid)
                conv.participants.add(user)
            except User.DoesNotExist:
                pass

        django_messages.success(request, f"Group '{name}' created.")
        return redirect('conversation_detail', conv_id=conv.id)

    return redirect('inbox')


# ── NOTIFICATIONS ──────────────────────────────────

@login_required
def notifications_view(request):
    """All notifications for the current user."""
    notifs = request.user.notifications.all()
    unread_count = notifs.filter(is_read=False).count()

    # Mark all as read when page is opened
    notifs.filter(is_read=False).update(is_read=True)

    context = {
        'notifications': notifs,
        'unread_count': unread_count,
        'active_page': 'notifications',
    }
    return render(request, 'messaging/notifications.html', context)


@login_required
def unread_counts_api(request):
    """JSON API — returns unread message + notification counts for the navbar badge."""
    unread_msgs = sum(
        c.unread_count(request.user)
        for c in request.user.conversations.all()
    )
    unread_notifs = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({
        'messages': unread_msgs,
        'notifications': unread_notifs,
        'total': unread_msgs + unread_notifs,
    })


@login_required
@require_POST
def mark_notification_read(request, notif_id):
    """Mark a single notification as read."""
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})
