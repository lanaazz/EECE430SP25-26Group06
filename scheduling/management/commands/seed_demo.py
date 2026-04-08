"""
Management command to seed the database with demo data.
Run with: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from scheduling.models import Team, UserProfile, Match, TrainingSession, Announcement


class Command(BaseCommand):
    help = 'Seed database with demo teams, users, matches, and training sessions'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # --- Teams ---
        team_a, _ = Team.objects.get_or_create(name='Thunder Spikes')
        team_b, _ = Team.objects.get_or_create(name='Blue Aces')
        team_c, _ = Team.objects.get_or_create(name='Golden Sets')
        self.stdout.write('  ✓ Teams created')

        # --- Users ---
        def make_user(username, password, role, team):
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.team = team
            profile.save()
            return user

        coach = make_user('coach1', 'coach123', 'coach', team_a)
        player1 = make_user('player1', 'player123', 'player', team_a)
        captain = make_user('captain1', 'captain123', 'captain', team_a)
        self.stdout.write('  ✓ Users created')
        self.stdout.write('    coach1 / coach123  (Coach)')
        self.stdout.write('    player1 / player123  (Player)')
        self.stdout.write('    captain1 / captain123  (Captain)')

        # --- Matches ---
        now = timezone.now()
        matches_data = [
            (team_a, team_b, now + timedelta(days=3, hours=2), 'Main Arena'),
            (team_b, team_c, now + timedelta(days=10, hours=3), 'Sports Complex'),
            (team_a, team_c, now + timedelta(days=18, hours=4), 'Main Arena'),
            (team_b, team_a, now - timedelta(days=5), 'Sports Complex'),
            (team_c, team_a, now - timedelta(days=12), 'Olympic Hang'),
        ]
        for home, away, date, loc in matches_data:
            Match.objects.get_or_create(
                home_team=home,
                away_team=away,
                date=date,
                defaults={
                    'location': loc,
                    'status': 'upcoming' if date > now else 'completed',
                    'created_by': coach,
                    'home_score': 3 if date < now else None,
                    'away_score': 1 if date < now else None,
                }
            )
        self.stdout.write('  ✓ Matches created')

        # --- Training Sessions ---
        trainings_data = [
            (team_a, 'Defensive Drills', now + timedelta(days=1, hours=5), 'Gym Hall A', 90),
            (team_a, 'Serve Practice', now + timedelta(days=4, hours=6), 'Gym Hall A', 60),
            (team_a, 'Team Tactics', now + timedelta(days=7, hours=5), 'Main Arena', 120),
            (team_b, 'Conditioning', now + timedelta(days=2, hours=7), 'Sports Complex', 90),
        ]
        for team, title, date, loc, duration in trainings_data:
            TrainingSession.objects.get_or_create(
                team=team,
                title=title,
                date=date,
                defaults={
                    'location': loc,
                    'duration_minutes': duration,
                    'created_by': coach,
                }
            )
        self.stdout.write('  ✓ Training sessions created')

        # --- Announcements ---
        Announcement.objects.get_or_create(
            team=team_a,
            title='Gym closure due to maintenance',
            defaults={
                'body': 'The gym will be closed on Feb 15 for scheduled maintenance. Training moved to Sports Complex.',
                'created_by': coach,
            }
        )
        Announcement.objects.get_or_create(
            team=team_a,
            title='New jerseys available',
            defaults={
                'body': 'New season jerseys are ready for pickup. Contact the manager.',
                'created_by': coach,
            }
        )
        self.stdout.write('  ✓ Announcements created')

        self.stdout.write(self.style.SUCCESS('\n✅ Demo data seeded successfully!'))
        self.stdout.write('\nLogin at /login/ with:')
        self.stdout.write('  coach1 / coach123  → full scheduling access')
        self.stdout.write('  player1 / player123  → view-only access')
