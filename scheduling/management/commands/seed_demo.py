"""
Management command to seed the database with demo data.
Run with: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from scheduling.models import Team, UserProfile, Match, TrainingSession, Announcement, Achievement, PlayerAchievement, News, Payment, MatchStats


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

        # Team A - Thunder Spikes
        coach_a = make_user('coach_thunder', 'coach123', 'coach', team_a)
        captain_a = make_user('captain_thunder', 'captain123', 'captain', team_a)
        players_a = []
        for i in range(1, 8):
            player = make_user(f'player_thunder{i}', 'player123', 'player', team_a)
            players_a.append(player)
        parents_a = []
        for i in range(1, 4):
            parent = make_user(f'parent_thunder{i}', 'parent123', 'parent', team_a)
            parents_a.append(parent)
        manager_a = make_user('manager_thunder', 'manager123', 'manager', team_a)
        
        # Team B - Blue Aces
        coach_b = make_user('coach_blue', 'coach123', 'coach', team_b)
        captain_b = make_user('captain_blue', 'captain123', 'captain', team_b)
        players_b = []
        for i in range(1, 8):
            player = make_user(f'player_blue{i}', 'player123', 'player', team_b)
            players_b.append(player)
        
        # Team C - Golden Sets
        coach_c = make_user('coach_gold', 'coach123', 'coach', team_c)
        captain_c = make_user('captain_gold', 'captain123', 'captain', team_c)
        players_c = []
        for i in range(1, 7):
            player = make_user(f'player_gold{i}', 'player123', 'player', team_c)
            players_c.append(player)
        
        self.stdout.write('  ✓ Users created')
        self.stdout.write(f'    Team A: 1 coach, 1 captain, 7 players, 3 parents, 1 manager')
        self.stdout.write(f'    Team B: 1 coach, 1 captain, 7 players')
        self.stdout.write(f'    Team C: 1 coach, 1 captain, 6 players')

        # --- Matches ---
        now = timezone.now()
        matches_data = [
            (team_a, team_b, now + timedelta(days=3, hours=2), 'Main Arena'),
            (team_b, team_c, now + timedelta(days=10, hours=3), 'Sports Complex'),
            (team_a, team_c, now + timedelta(days=18, hours=4), 'Main Arena'),
            (team_b, team_a, now - timedelta(days=5), 'Sports Complex'),
            (team_c, team_a, now - timedelta(days=12), 'Olympic Hang'),
            (team_a, team_b, now - timedelta(days=25), 'Main Arena'),
            (team_b, team_c, now - timedelta(days=32), 'Sports Complex'),
        ]
        matches = []
        for home, away, date_time, loc in matches_data:
            match, _ = Match.objects.get_or_create(
                home_team=home,
                away_team=away,
                date=date_time,
                defaults={
                    'location': loc,
                    'status': 'upcoming' if date_time > now else 'completed',
                    'created_by': coach_a,
                    'home_score': 3 if date_time < now else None,
                    'away_score': 1 if date_time < now else None,
                }
            )
            matches.append(match)
        
        # Add MatchStats to completed matches
        for idx, match in enumerate(matches):
            if match.status == 'completed':
                MatchStats.objects.get_or_create(
                    match=match,
                    defaults={
                        'home_strikes': 47 + (idx * 3),
                        'home_blocks': 12 + (idx * 1),
                        'home_service_aces': 5 + idx,
                        'home_errors': 8 + idx,
                        'away_strikes': 38 + (idx * 2),
                        'away_blocks': 10 + idx,
                        'away_service_aces': 3 + idx,
                        'away_errors': 12 + (idx * 2),
                    }
                )
        self.stdout.write('  ✓ Matches created with stats')

        # --- Training Sessions ---
        trainings_data = [
            (team_a, 'Defensive Drills', now + timedelta(days=1, hours=5), 'Gym Hall A', 90),
            (team_a, 'Serve Practice', now + timedelta(days=4, hours=6), 'Gym Hall A', 60),
            (team_a, 'Team Tactics', now + timedelta(days=7, hours=5), 'Main Arena', 120),
            (team_b, 'Conditioning', now + timedelta(days=2, hours=7), 'Sports Complex', 90),
            (team_b, 'Block Techniques', now + timedelta(days=8, hours=6), 'Gym Hall B', 75),
            (team_c, 'Speed & Agility', now + timedelta(days=5, hours=5), 'Main Arena', 100),
        ]
        for team, title, date_time, loc, duration in trainings_data:
            TrainingSession.objects.get_or_create(
                team=team,
                title=title,
                date=date_time,
                defaults={
                    'location': loc,
                    'duration_minutes': duration,
                    'created_by': coach_a,
                }
            )
        self.stdout.write('  ✓ Training sessions created')

        # --- Announcements ---
        Announcement.objects.get_or_create(
            team=team_a,
            title='Gym closure due to maintenance',
            defaults={
                'body': 'The gym will be closed on Feb 15 for scheduled maintenance. Training moved to Sports Complex.',
                'created_by': coach_a,
            }
        )
        Announcement.objects.get_or_create(
            team=team_a,
            title='New jerseys available',
            defaults={
                'body': 'New season jerseys are ready for pickup. Contact the manager.',
                'created_by': coach_a,
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
            player=players_a[0],
            achievement=achievements['MVP'],
            defaults={'awarded_by': coach_a, 'notes': 'Outstanding performance in the last match'}
        )
        PlayerAchievement.objects.get_or_create(
            player=players_a[0],
            achievement=achievements['Best Serve'],
            defaults={'awarded_by': coach_a}
        )
        PlayerAchievement.objects.get_or_create(
            player=players_a[1],
            achievement=achievements['Defense Star'],
            defaults={'awarded_by': coach_a}
        )
        PlayerAchievement.objects.get_or_create(
            player=captain_a,
            achievement=achievements['Team Spirit'],
            defaults={'awarded_by': coach_a}
        )
        self.stdout.write('  ✓ Player achievements created')

        # --- News/Links ---
        News.objects.get_or_create(
            team=team_a,
            title='Team Training Guide',
            url='https://www.youtube.com/watch?v=PZSvPJJX2-I',
            defaults={
                'description': 'Essential volleyball training techniques and drills',
                'created_by': coach_a,
            }
        )
        News.objects.get_or_create(
            team=team_a,
            title='Volleyball Rules & Regulations',
            url='https://www.fivb.org/',
            defaults={
                'description': 'Official FIVB rules and international volleyball standards',
                'created_by': coach_a,
            }
        )
        self.stdout.write('  ✓ News links created')

        # --- Payments (Demo) ---
        # Create payments for all team A players with varying statuses and amounts
        payment_months = [
            date.today() + timedelta(days=30),  # Due next month
            date.today() + timedelta(days=60),  # Due 2 months from now
            date.today() - timedelta(days=10),  # Due 10 days ago (can be paid)
            date.today() - timedelta(days=40),  # Due 40 days ago
        ]
        
        all_team_a_members = [captain_a] + players_a + parents_a
        for member in all_team_a_members:
            if member.profile.role in ['player', 'captain', 'parent']:
                for idx, due_date in enumerate(payment_months):
                    # Vary the payment status - some paid, some pending
                    is_paid = idx < 2  # First two are paid
                    Payment.objects.get_or_create(
                        player=member,
                        due_date=due_date,
                        defaults={
                            'amount': 150.00,
                            'status': 'paid' if is_paid else 'pending',
                            'paid_date': date.today() - timedelta(days=15) if is_paid else None
                        }
                    )
        
        # Create payments for team B players
        for player in [captain_b] + players_b:
            for idx, due_date in enumerate(payment_months[:2]):  # Just 2 payments for demo
                Payment.objects.get_or_create(
                    player=player,
                    due_date=due_date,
                    defaults={
                        'amount': 150.00,
                        'status': 'paid' if idx == 0 else 'pending',
                        'paid_date': date.today() - timedelta(days=5) if idx == 0 else None
                    }
                )
        
        self.stdout.write('  ✓ Payment records created')

        self.stdout.write(self.style.SUCCESS('\n✅ Demo data seeded successfully!'))
        self.stdout.write('\nLogin at /login/ with:')
        self.stdout.write('  coach1 / coach123  → manage team, achievements, news')
        self.stdout.write('  player1 / player123  → view achievements and payments')
        self.stdout.write('  parent1 / parent123  → manage player payments')
        self.stdout.write('  manager1 / manager123  → manage player payments')
