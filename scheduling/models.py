from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Team(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('player', 'Player'),
        ('captain', 'Captain'),
        ('coach', 'Coach'),
        ('parent', 'Parent'),
        ('manager', 'Manager'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='player')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Match(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_matches')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} — {self.date.strftime('%b %d %Y')}"

    @property
    def is_upcoming(self):
        return self.date > timezone.now() and self.status == 'upcoming'


class TrainingSession(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='training_sessions')
    title = models.CharField(max_length=200)
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    duration_minutes = models.IntegerField(default=90)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_trainings')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} — {self.date.strftime('%b %d %Y %H:%M')}"

    @property
    def is_upcoming(self):
        return self.date > timezone.now() and self.status == 'scheduled'


class Announcement(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
