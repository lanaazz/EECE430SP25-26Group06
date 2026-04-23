from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone

from scheduling.models import Team, UserProfile, Match, TrainingSession, Announcement
from .serializers import (
    TeamSerializer, UserSerializer, RegisterSerializer,
    MatchSerializer, TrainingSessionSerializer, AnnouncementSerializer,
)
from .permissions import IsCoach, IsCoachOrReadOnly


# ─────────────────────────────────────────────
# AUTH ENDPOINTS
# ─────────────────────────────────────────────

class RegisterAPIView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Register a new user and return their auth token.
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns auth token + user info.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)
        # Create profile if missing (e.g. superuser)
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user, role='player')

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        })


class LogoutAPIView(APIView):
    """
    POST /api/auth/logout/
    Deletes the user's auth token (invalidates session).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'message': 'Logged out successfully.'})


class MeAPIView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/me/   — get current user profile
    PUT  /api/auth/me/   — update current user profile
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# ─────────────────────────────────────────────
# TEAM ENDPOINTS
# ─────────────────────────────────────────────

class TeamViewSet(viewsets.ModelViewSet):
    """
    GET    /api/teams/         — list all teams
    POST   /api/teams/         — create team (coach only)
    GET    /api/teams/{id}/    — retrieve team
    PUT    /api/teams/{id}/    — update team (coach only)
    DELETE /api/teams/{id}/    — delete team (coach only)
    GET    /api/teams/{id}/members/ — list team members
    """
    queryset = Team.objects.all().order_by('name')
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsCoachOrReadOnly]

    @action(detail=True, methods=['get'], url_path='members')
    def members(self, request, pk=None):
        team = self.get_object()
        profiles = UserProfile.objects.filter(team=team).select_related('user')
        data = [
            {
                'id': p.user.id,
                'username': p.user.username,
                'full_name': p.user.get_full_name() or p.user.username,
                'role': p.role,
                'role_display': p.get_role_display(),
            }
            for p in profiles
        ]
        return Response(data)


# ─────────────────────────────────────────────
# MATCH ENDPOINTS
# ─────────────────────────────────────────────

class MatchViewSet(viewsets.ModelViewSet):
    """
    GET    /api/matches/              — list all matches
    POST   /api/matches/              — create match (coach only)
    GET    /api/matches/{id}/         — retrieve match
    PUT    /api/matches/{id}/         — update match (coach only)
    DELETE /api/matches/{id}/         — delete match (coach only)
    GET    /api/matches/upcoming/     — upcoming matches only
    POST   /api/matches/{id}/cancel/  — cancel a match (coach only)
    """
    queryset = Match.objects.all().select_related('home_team', 'away_team', 'created_by')
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated, IsCoachOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date', 'status']
    ordering = ['date']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        team_param = self.request.query_params.get('team')
        if status_param:
            qs = qs.filter(status=status_param)
        if team_param:
            qs = qs.filter(home_team_id=team_param) | qs.filter(away_team_id=team_param)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming(self, request):
        qs = Match.objects.filter(
            date__gte=timezone.now(), status='upcoming'
        ).select_related('home_team', 'away_team').order_by('date')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancel',
            permission_classes=[IsAuthenticated, IsCoach])
    def cancel(self, request, pk=None):
        match = self.get_object()
        if match.status == 'cancelled':
            return Response({'error': 'Match is already cancelled.'}, status=400)
        match.status = 'cancelled'
        match.save()
        return Response({'message': 'Match cancelled.', 'match': MatchSerializer(match).data})


# ─────────────────────────────────────────────
# TRAINING SESSION ENDPOINTS
# ─────────────────────────────────────────────

class TrainingSessionViewSet(viewsets.ModelViewSet):
    """
    GET    /api/trainings/              — list all training sessions
    POST   /api/trainings/              — create session (coach only)
    GET    /api/trainings/{id}/         — retrieve session
    PUT    /api/trainings/{id}/         — update session (coach only)
    DELETE /api/trainings/{id}/         — delete session (coach only)
    GET    /api/trainings/upcoming/     — upcoming sessions only
    POST   /api/trainings/{id}/cancel/  — cancel a session (coach only)
    """
    queryset = TrainingSession.objects.all().select_related('team', 'created_by')
    serializer_class = TrainingSessionSerializer
    permission_classes = [IsAuthenticated, IsCoachOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering = ['date']

    def get_queryset(self):
        qs = super().get_queryset()
        team_param = self.request.query_params.get('team')
        status_param = self.request.query_params.get('status')
        if team_param:
            qs = qs.filter(team_id=team_param)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming(self, request):
        qs = TrainingSession.objects.filter(
            date__gte=timezone.now(), status='scheduled'
        ).select_related('team').order_by('date')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancel',
            permission_classes=[IsAuthenticated, IsCoach])
    def cancel(self, request, pk=None):
        session = self.get_object()
        if session.status == 'cancelled':
            return Response({'error': 'Session is already cancelled.'}, status=400)
        session.status = 'cancelled'
        session.save()
        return Response({'message': 'Training session cancelled.',
                         'session': TrainingSessionSerializer(session).data})


# ─────────────────────────────────────────────
# ANNOUNCEMENT ENDPOINTS
# ─────────────────────────────────────────────

class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    GET    /api/announcements/       — list announcements
    POST   /api/announcements/       — create (coach only)
    GET    /api/announcements/{id}/  — retrieve
    PUT    /api/announcements/{id}/  — update (coach only)
    DELETE /api/announcements/{id}/  — delete (coach only)
    """
    queryset = Announcement.objects.all().select_related('team', 'created_by')
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated, IsCoachOrReadOnly]
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        team_param = self.request.query_params.get('team')
        if team_param:
            qs = qs.filter(team_id=team_param)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ─────────────────────────────────────────────
# DASHBOARD SUMMARY ENDPOINT
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """
    GET /api/dashboard/
    Returns upcoming matches, trainings, and announcements for the current user's team.
    """
    now = timezone.now()
    profile = getattr(request.user, 'profile', None)
    team = profile.team if profile else None

    upcoming_matches = Match.objects.filter(
        date__gte=now, status='upcoming'
    ).select_related('home_team', 'away_team').order_by('date')[:5]

    upcoming_trainings = TrainingSession.objects.filter(
        date__gte=now, status='scheduled'
    ).select_related('team').order_by('date')[:5]

    announcements = []
    if team:
        announcements = Announcement.objects.filter(team=team).order_by('-created_at')[:5]

    return Response({
        'user': UserSerializer(request.user).data,
        'upcoming_matches': MatchSerializer(upcoming_matches, many=True).data,
        'upcoming_trainings': TrainingSessionSerializer(upcoming_trainings, many=True).data,
        'announcements': AnnouncementSerializer(announcements, many=True).data,
    })
