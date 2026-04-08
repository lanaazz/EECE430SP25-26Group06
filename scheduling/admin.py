from django.contrib import admin
from .models import Team, UserProfile, Match, TrainingSession, Announcement


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'team']
    list_filter = ['role', 'team']
    search_fields = ['user__username']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'date', 'location', 'status', 'created_by']
    list_filter = ['status', 'home_team', 'away_team']
    search_fields = ['home_team__name', 'away_team__name', 'location']
    date_hierarchy = 'date'


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'team', 'date', 'location', 'duration_minutes', 'status']
    list_filter = ['status', 'team']
    search_fields = ['title', 'location']
    date_hierarchy = 'date'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'team', 'created_by', 'created_at']
    list_filter = ['team']
