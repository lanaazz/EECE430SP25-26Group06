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
        ('live', 'Live'),
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

class Payment(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
    ]

    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.player.username} - {self.status} - ${self.amount}"


class Achievement(models.Model):
    """Achievement badges that can be awarded to players."""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='achievements')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='🏆')  # emoji or icon name
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('team', 'name')

    def __str__(self):
        return f"{self.name} ({self.team.name})"


class PlayerAchievement(models.Model):
    """Relationship between players and achievements."""
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='awarded_to')
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='awarded_achievements')
    awarded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-awarded_at']
        unique_together = ('player', 'achievement')

    def __str__(self):
        return f"{self.player.username} — {self.achievement.name}"


class News(models.Model):
    """News and links shared by coaches with their team."""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='news')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url = models.URLField()
    # For YouTube thumbnails or custom images
    thumbnail_url = models.URLField(blank=True, help_text="URL to thumbnail image. YouTube links auto-generate.")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_news')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.team.name})"

    def get_thumbnail(self):
        """Return thumbnail URL, auto-generate from YouTube if needed."""
        if self.thumbnail_url:
            return self.thumbnail_url
        
        # Auto-extract YouTube thumbnail
        if 'youtube.com' in self.url or 'youtu.be' in self.url:
            video_id = None
            if 'youtube.com' in self.url:
                video_id = self.url.split('v=')[1].split('&')[0] if 'v=' in self.url else None
            elif 'youtu.be' in self.url:
                video_id = self.url.split('youtu.be/')[1].split('?')[0] if 'youtu.be/' in self.url else None
            
            if video_id:
                return f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg'
        
        return None


class MatchStats(models.Model):
    """Statistics for a match - tracks strikes, blocks, service aces, etc."""
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='stats')
    
    # Home team stats
    home_strikes = models.IntegerField(default=0, help_text="Successful attacks/strikes")
    home_blocks = models.IntegerField(default=0, help_text="Successful blocks")
    home_service_aces = models.IntegerField(default=0, help_text="Service aces (unreturnable serves)")
    home_errors = models.IntegerField(default=0, help_text="Unforced errors")
    
    # Away team stats
    away_strikes = models.IntegerField(default=0, help_text="Successful attacks/strikes")
    away_blocks = models.IntegerField(default=0, help_text="Successful blocks")
    away_service_aces = models.IntegerField(default=0, help_text="Service aces (unreturnable serves)")
    away_errors = models.IntegerField(default=0, help_text="Unforced errors")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats for {self.match}"


class PlayerMatchStats(models.Model):
    """Per-player statistics for a specific match (SCRUM-15)."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='player_stats')
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_stats')
    strikes = models.IntegerField(default=0, help_text="Successful attacks/strikes")
    blocks = models.IntegerField(default=0, help_text="Successful blocks")
    service_aces = models.IntegerField(default=0, help_text="Service aces")
    errors = models.IntegerField(default=0, help_text="Unforced errors")
    digs = models.IntegerField(default=0, help_text="Successful digs")
    assists = models.IntegerField(default=0, help_text="Assists")
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_stats')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['player__username']
        unique_together = ('match', 'player')

    def __str__(self):
        return f"{self.player.username} stats for {self.match}"


class SessionAttendance(models.Model):
    """Tracks player attendance for training sessions (SCRUM-17)."""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    ]
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='attendance_records')
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_attendance')
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['player__username']
        unique_together = ('session', 'player')

    def __str__(self):
        return f"{self.player.username} — {self.session.title} — {self.status}"