import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Q
from scheduling.models import Match, PlayerMatchStats, UserProfile


PLAYER_PROFILES = {
    # profile_key: (strikes, blocks, aces, digs, assists, errors) as (min, max) tuples
    'attacker':      [(12, 22), (3, 7),  (2, 5),  (4, 9),  (2, 5),  (2, 6)],
    'blocker':       [(6, 12),  (8, 14), (1, 4),  (4, 8),  (3, 6),  (1, 4)],
    'setter':        [(3, 8),   (2, 5),  (2, 5),  (6, 11), (12, 18),(2, 5)],
    'libero':        [(2, 5),   (1, 3),  (1, 3),  (12, 18),(4, 8),  (1, 3)],
    'all_rounder':   [(8, 16),  (5, 10), (2, 6),  (7, 12), (5, 10), (2, 5)],
    'server':        [(7, 13),  (4, 8),  (4, 8),  (5, 10), (4, 8),  (2, 5)],
}

PLAYER_ROLE_MAP = {
    # Thunder Spikes
    'captain_thunder':  'all_rounder',
    'player_thunder1':  'attacker',
    'player_thunder2':  'blocker',
    'player_thunder3':  'setter',
    'player_thunder4':  'libero',
    'player_thunder5':  'attacker',
    'player_thunder6':  'server',
    'player_thunder7':  'all_rounder',
    # Blue Aces
    'captain_blue':     'all_rounder',
    'player_blue1':     'attacker',
    'player_blue2':     'setter',
    'player_blue3':     'blocker',
    'player_blue4':     'libero',
    'player_blue5':     'attacker',
    'player_blue6':     'server',
    'player_blue7':     'all_rounder',
    # Golden Sets
    'captain_gold':     'all_rounder',
    'player_gold1':     'attacker',
    'player_gold2':     'setter',
    'player_gold3':     'blocker',
    'player_gold4':     'libero',
    'player_gold5':     'server',
    'player_gold6':     'all_rounder',
}


def stat_for(username, field_idx, match_id):
    profile_key = PLAYER_ROLE_MAP.get(username, 'all_rounder')
    lo, hi = PLAYER_PROFILES[profile_key][field_idx]
    rng = random.Random(f"{username}_{match_id}_{field_idx}")
    return rng.randint(lo, hi)


class Command(BaseCommand):
    help = 'Seed demo PlayerMatchStats for captain_thunder, player_thunder1-7, player_blue1-7, player_gold1-6'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing stats before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = PlayerMatchStats.objects.filter(
                player__username__in=list(PLAYER_ROLE_MAP.keys())
            ).delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} existing stats records'))

        target_usernames = list(PLAYER_ROLE_MAP.keys())
        players = {u.username: u for u in User.objects.filter(username__in=target_usernames)}

        missing = set(target_usernames) - set(players.keys())
        if missing:
            self.stdout.write(self.style.WARNING(f'Users not found in DB: {sorted(missing)}'))

        completed_matches = Match.objects.filter(status='completed').select_related(
            'home_team', 'away_team'
        ).order_by('date')

        # Build team -> player list mapping
        team_players: dict = {}
        for uname, user_obj in players.items():
            try:
                profile = user_obj.profile
                if profile.team_id:
                    team_players.setdefault(profile.team_id, []).append(user_obj)
            except Exception:
                pass

        created_count = 0
        skipped_count = 0

        for match in completed_matches:
            involved_team_ids = {match.home_team_id, match.away_team_id}
            match_players = []
            for tid in involved_team_ids:
                match_players.extend(team_players.get(tid, []))

            for player in match_players:
                uname = player.username
                defaults = {
                    'strikes':      stat_for(uname, 0, match.id),
                    'blocks':       stat_for(uname, 1, match.id),
                    'service_aces': stat_for(uname, 2, match.id),
                    'digs':         stat_for(uname, 3, match.id),
                    'assists':      stat_for(uname, 4, match.id),
                    'errors':       stat_for(uname, 5, match.id),
                }
                _, created = PlayerMatchStats.objects.get_or_create(
                    match=match,
                    player=player,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created {created_count} records, skipped {skipped_count} existing.'
        ))