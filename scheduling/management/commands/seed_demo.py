"""
Management command to seed the database with demo data.
Run with: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from scheduling.models import Team, UserProfile, Match, TrainingSession, Announcement, Achievement, PlayerAchievement, News, Payment


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
        player2 = make_user('player2', 'player123', 'player', team_a)
        captain = make_user('captain1', 'captain123', 'captain', team_a)
        parent = make_user('parent1', 'parent123', 'parent', team_a)
        manager = make_user('manager1', 'manager123', 'manager', team_a)
        self.stdout.write('  ✓ Users created')
        self.stdout.write('    coach1 / coach123  (Coach)')
        self.stdout.write('    player1 / player123  (Player)')
        self.stdout.write('    player2 / player123  (Player)')
        self.stdout.write('    captain1 / captain123  (Captain)')
        self.stdout.write('    parent1 / parent123  (Parent)')
        self.stdout.write('    manager1 / manager123  (Manager)')

        # --- Matches ---
        now = timezone.now()
        matches_data = [
            (team_a, team_b, now + timedelta(days=3, hours=2), 'Main Arena'),
            (team_b, team_c, now + timedelta(days=10, hours=3), 'Sports Complex'),
            (team_a, team_c, now + timedelta(days=18, hours=4), 'Main Arena'),
            (team_b, team_a, now - timedelta(days=5), 'Sports Complex'),
            (team_c, team_a, now - timedelta(days=12), 'Olympic Hang'),
        ]
        for home, away, date_time, loc in matches_data:
            Match.objects.get_or_create(
                home_team=home,
                away_team=away,
                date=date_time,
                defaults={
                    'location': loc,
                    'status': 'upcoming' if date_time > now else 'completed',
                    'created_by': coach,
                    'home_score': 3 if date_time < now else None,
                    'away_score': 1 if date_time < now else None,
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
        for team, title, date_time, loc, duration in trainings_data:
            TrainingSession.objects.get_or_create(
                team=team,
                title=title,
                date=date_time,
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

        # --- Achievements ---
        achievements_data = [
            ('MVP', '🏆', 'Most Valuable Player award'),
            ('Best Serve', '⚡', 'Outstanding serving performance'),
            ('Defense Star', '🛡️', 'Excellent defensive plays'),
            ('Team Spirit', '💪', 'Great team collaboration'),
            ('Perfect Attendance', '✅', 'Attended all trainings'),
        ]
        achievements = {}
        for name, icon, desc in achievements_data:
            ach, _ = Achievement.objects.get_or_create(
                team=team_a,
                name=name,
                defaults={'icon': icon, 'description': desc}
            )
            achievements[name] = ach
        self.stdout.write('  ✓ Achievements created')

        # --- Player Achievements ---
        PlayerAchievement.objects.get_or_create(
            player=player1,
            achievement=achievements['MVP'],
            defaults={'awarded_by': coach, 'notes': 'Outstanding performance in the last match'}
        )
        PlayerAchievement.objects.get_or_create(
            player=player1,
            achievement=achievements['Best Serve'],
            defaults={'awarded_by': coach}
        )
        PlayerAchievement.objects.get_or_create(
            player=player2,
            achievement=achievements['Defense Star'],
            defaults={'awarded_by': coach}
        )
        PlayerAchievement.objects.get_or_create(
            player=captain,
            achievement=achievements['Team Spirit'],
            defaults={'awarded_by': coach}
        )
        self.stdout.write('  ✓ Player achievements created')

        # --- News/Links ---
        News.objects.get_or_create(
            team=team_a,
            title='Team Training Guide',
            url='https://www.youtube.com/watch?v=PZSvPJJX2-I',
            defaults={
                'description': 'Essential volleyball training techniques and drills',
                'created_by': coach,
            }
        )
        News.objects.get_or_create(
            team=team_a,
            title='Volleyball Rules & Regulations',
            url='https://www.fivb.org/',
            defaults={
                'description': 'Official FIVB rules and international volleyball standards',
                'created_by': coach,
            }
        )
        self.stdout.write('  ✓ News links created')

        # --- Payments (Demo) ---
        due_date_1 = date.today() + timedelta(days=30)
        due_date_2 = date.today() + timedelta(days=60)
        
        Payment.objects.get_or_create(
            player=player1,
            due_date=due_date_1,
            defaults={'amount': 150.00, 'status': 'pending'}
        )
        Payment.objects.get_or_create(
            player=player1,
            due_date=due_date_2,
            defaults={'amount': 150.00, 'status': 'pending'}
        )
        Payment.objects.get_or_create(
            player=player2,
            due_date=due_date_1,
            defaults={'amount': 150.00, 'status': 'pending'}
        )
        Payment.objects.get_or_create(
            player=captain,
            due_date=due_date_1,
            defaults={'amount': 150.00, 'status': 'paid', 'paid_date': date.today() - timedelta(days=10)}
        )
        self.stdout.write('  ✓ Payment records created')

        self.stdout.write(self.style.SUCCESS('\n✅ Demo data seeded successfully!'))
        self.stdout.write('\nLogin at /login/ with:')
        self.stdout.write('  coach1 / coach123  → manage team, achievements, news')
        self.stdout.write('  player1 / player123  → view achievements and payments')
        self.stdout.write('  parent1 / parent123  → manage player payments')
        self.stdout.write('  manager1 / manager123  → manage player payments')
