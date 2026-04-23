"""
Signals to create notifications when matches and trainings are created.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Match, TrainingSession
from messaging.models import Notification


@receiver(post_save, sender=Match)
def notify_match_created(sender, instance, created, **kwargs):
    """Create notifications for all team members when a match is scheduled."""
    if not created:
        return  # Only notify on creation

    # Notify home team members
    home_team_members = instance.home_team.members.all()
    for member in home_team_members:
        Notification.objects.create(
            user=member.user,
            type='match',
            title=f"New Match: {instance.home_team.name} vs {instance.away_team.name}",
            body=f"Match scheduled for {instance.date.strftime('%b %d, %Y at %H:%M')} at {instance.location}",
            link=f"/matches/",
        )

    # Notify away team members
    away_team_members = instance.away_team.members.all()
    for member in away_team_members:
        Notification.objects.create(
            user=member.user,
            type='match',
            title=f"New Match: {instance.home_team.name} vs {instance.away_team.name}",
            body=f"Match scheduled for {instance.date.strftime('%b %d, %Y at %H:%M')} at {instance.location}",
            link=f"/matches/",
        )


@receiver(post_save, sender=TrainingSession)
def notify_training_created(sender, instance, created, **kwargs):
    """Create notifications for all team members when a training is scheduled."""
    if not created:
        return  # Only notify on creation

    # Notify all team members
    team_members = instance.team.members.all()
    for member in team_members:
        Notification.objects.create(
            user=member.user,
            type='training',
            title=f"New Training: {instance.title}",
            body=f"Training scheduled for {instance.date.strftime('%b %d, %Y at %H:%M')} at {instance.location}",
            link=f"/calendar/",
        )
