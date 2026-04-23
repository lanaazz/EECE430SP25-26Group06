from django.db import models
from django.contrib.auth.models import User
from scheduling.models import Team


class Conversation(models.Model):
    """A conversation between two or more users (DM or group)."""
    TYPE_CHOICES = [
        ('direct',  'Direct Message'),
        ('group',   'Group Chat'),
        ('team',    'Team Chat'),
    ]
    type        = models.CharField(max_length=10, choices=TYPE_CHOICES, default='direct')
    name        = models.CharField(max_length=100, blank=True)  # for group/team chats
    team        = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='conversations')
    participants= models.ManyToManyField(User, related_name='conversations')
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_conversations')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.type == 'direct':
            names = ', '.join(p.username for p in self.participants.all()[:2])
            return f"DM: {names}"
        return self.name or f"Group {self.id}"

    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count(self, user):
        return self.messages.exclude(read_by=user).exclude(sender=user).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body         = models.TextField()
    created_at   = models.DateTimeField(auto_now_add=True)
    read_by      = models.ManyToManyField(User, related_name='read_messages', blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.body[:40]}"

    def mark_read(self, user):
        self.read_by.add(user)


class Notification(models.Model):
    TYPE_CHOICES = [
        ('message',     'New Message'),
        ('match',       'Match Scheduled'),
        ('training',    'Training Scheduled'),
        ('announcement','Announcement'),
        ('system',      'System'),
    ]
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    title      = models.CharField(max_length=200)
    body       = models.TextField(blank=True)
    is_read    = models.BooleanField(default=False)
    link       = models.CharField(max_length=200, blank=True)  # URL to navigate to
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.title}"
