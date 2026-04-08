from rest_framework import serializers
from django.contrib.auth.models import User
from scheduling.models import Team, UserProfile, Match, TrainingSession, Announcement


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['role', 'role_display', 'team', 'team_name']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True)
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role', 'team']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        role = validated_data.pop('role')
        team = validated_data.pop('team', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(user=user, role=role, team=team)
        return user


class MatchSerializer(serializers.ModelSerializer):
    home_team_name = serializers.CharField(source='home_team.name', read_only=True)
    away_team_name = serializers.CharField(source='away_team.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'home_team', 'home_team_name',
            'away_team', 'away_team_name',
            'date', 'location', 'status',
            'home_score', 'away_score',
            'notes', 'is_upcoming',
            'created_by', 'created_by_username', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_by_username', 'created_at', 'is_upcoming']

    def validate(self, data):
        home = data.get('home_team')
        away = data.get('away_team')
        if home and away and home == away:
            raise serializers.ValidationError("Home team and away team cannot be the same.")
        return data


class TrainingSessionSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = TrainingSession
        fields = [
            'id', 'team', 'team_name', 'title',
            'date', 'location', 'duration_minutes',
            'status', 'description', 'is_upcoming',
            'created_by', 'created_by_username', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_by_username', 'created_at', 'is_upcoming']


class AnnouncementSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'team', 'team_name', 'title', 'body', 'created_by', 'created_by_username', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_by_username', 'created_at']


# ── Messaging serializers ──────────────────────────
from messaging.models import Conversation, Message, Notification


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_username', 'body', 'created_at']
        read_only_fields = ['id', 'sender', 'sender_username', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    participants_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'type', 'name', 'team', 'participants_count', 'last_message', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_participants_count(self, obj):
        return obj.participants.count()

    def get_last_message(self, obj):
        msg = obj.last_message()
        if msg:
            return {'sender': msg.sender.username, 'body': msg.body[:60], 'created_at': msg.created_at}
        return None


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'body', 'is_read', 'link', 'created_at']
        read_only_fields = ['id', 'created_at']
