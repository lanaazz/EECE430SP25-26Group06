from django.contrib import admin
from .models import Team, UserProfile, Match, TrainingSession, Announcement, Payment, Achievement, PlayerAchievement, News, MatchStats


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

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['player', 'amount', 'status', 'due_date', 'paid_date']
    list_filter = ['status']
    search_fields = ['player__username']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'icon', 'created_at']
    list_filter = ['team']
    search_fields = ['name']


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ['player', 'achievement', 'awarded_by', 'awarded_at']
    list_filter = ['achievement', 'awarded_at']
    search_fields = ['player__username', 'achievement__name']
    date_hierarchy = 'awarded_at'


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'team', 'created_by', 'created_at', 'url']
    list_filter = ['team', 'created_at']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'


@admin.register(MatchStats)
class MatchStatsAdmin(admin.ModelAdmin):
    list_display = ['match', 'home_strikes', 'home_blocks', 'away_strikes', 'away_blocks']
    list_filter = ['match__home_team', 'match__away_team']
    search_fields = ['match__home_team__name', 'match__away_team__name']
    date_hierarchy = 'created_at'