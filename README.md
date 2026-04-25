# Volleyball Platform

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply migrations
python manage.py migrate

# 3. Seed demo data (teams, users, matches, trainings, achievements, payments, news)
python manage.py seed_demo

# 4. Seed player statistics data (per-match performance metrics)
python manage.py seed_player_stats

# 5. Run the development server
python manage.py runserver
```

Then open http://127.0.0.1:8000/login/

---

## Demo Accounts

### Team A — Thunder Spikes

| Username | Password | Role | Access |
|---|---|---|---|
| `coach_thunder` | `coach123` | Coach | Full access: schedule matches & trainings, manage team members, create & award achievements, view all stats |
| `captain_thunder` | `captain123` | Captain | View calendar, matches, statistics, achievements |
| `player_thunder1` – `player_thunder7` | `player123` | Player | View calendar, matches, statistics, own achievements & payments |
| `parent_thunder1` – `parent_thunder3` | `parent123` | Parent | View & manage payments for team players |
| `manager_thunder` | `manager123` | Manager | Manage team members + payment management |

### Team B — Blue Aces

| Username | Password | Role | Access |
|---|---|---|---|
| `coach_blue` | `coach123` | Coach | Full coach access for Blue Aces |
| `captain_blue` | `captain123` | Captain | View-only |
| `player_blue1` – `player_blue7` | `player123` | Player | View-only |

### Team C — Golden Sets

| Username | Password | Role | Access |
|---|---|---|---|
| `coach_gold` | `coach123` | Coach | Full coach access for Golden Sets |
| `captain_gold` | `captain123` | Captain | View-only |
| `player_gold1` – `player_gold6` | `player123` | Player | View-only |

---

## Features

### Scheduling
- Monthly calendar view with match and training session events
- Coaches can create, edit, and cancel matches and training sessions
- Clicking calendar events navigates to match/training detail pages
- Events are filtered to the logged-in user's team

### Matches
- Upcoming and past match listings
- Match detail page with scores and per-team statistics (strikes, blocks, service aces, errors)
- Coach controls: edit and cancel matches inline

### Training Sessions
- Training detail page showing duration, location, description, organiser, and estimated end time
- Scheduled, completed, and cancelled statuses

### Statistics
- **Player Performance Graphs** (role-based):
  - Coach / Manager: Select any player to view their graphs
  - Parent: Select team players to monitor their progress
  - Player / Captain: View only their own stats
- Season profile radar chart (all 6 stats: strikes, blocks, aces, digs, assists, errors)
- Per-match breakdown bar chart (strikes, blocks, digs, assists by match)
- Performance trend line chart (4-metric trends over matches)
- Match-by-match detailed stats table
- Season totals summary cards
- **See [PLAYER_STATISTICS.md](PLAYER_STATISTICS.md) for full documentation**

### Achievements
- Coaches create badge types (name, emoji icon, description) per team
- Coaches award badges to individual players with optional notes
- Players see their own awarded achievements and available badges

### Payments
- Players view their own payment records (pending / paid)
- Parents and managers can browse team players and mark payments as paid (demo)

### News
- Coaches share links and YouTube videos with their team
- YouTube thumbnails are auto-generated from the video URL
- All team members can view shared news cards

### Messaging & Notifications
- Direct messages between team members
- Group chat creation (coaches/managers can message anyone; players are team-scoped)
- Unread badge counts in the sidebar and notification bell
- Automatic notifications on new matches, trainings, and messages

### REST API
- Token-based authentication (`/api/auth/login/`, `/api/auth/register/`)
- Full CRUD for teams, matches, training sessions, and announcements
- Coach-only write permissions via `IsCoachOrReadOnly`
- Interactive API Explorer at `/api/`

---

## Project Structure

```
volleyball/
├── manage.py
├── requirements.txt
│
├── scheduling/                         # Core domain models & views
│   ├── models.py                       # Team, UserProfile, Match, TrainingSession,
│   │                                   # Announcement, Payment, Achievement,
│   │                                   # PlayerAchievement, News, MatchStats
│   ├── views.py                        # Calendar, match/training detail, scheduling,
│   │                                   # payments, win-rate
│   ├── forms.py                        # MatchForm, TrainingSessionForm, MatchStatsForm
│   ├── urls.py
│   ├── admin.py
│   ├── signals.py                      # Auto-notifications on match/training creation
│   ├── apps.py
│   ├── migrations/
│   └── management/commands/
│       ├── seed_demo.py                # Populates all demo data
│       └── seed_player_stats.py        # Generates PlayerMatchStats records for demo
│
├── accounts/                           # Auth & user management
│   ├── views.py                        # Login, logout, register, profile,
│   │                                   # change password, manage team members
│   ├── forms.py                        # RegisterForm, ProfileUpdateForm, ChangePasswordForm
│   ├── urls.py
│   └── migrations/
│
├── messaging/                          # Conversations & notifications
│   ├── models.py                       # Conversation, Message, Notification
│   ├── views.py                        # Inbox, conversation detail, DM, group chat,
│   │                                   # notifications, unread counts API
│   ├── urls.py
│   └── migrations/
│
├── api/                                # REST API (Django REST Framework)
│   ├── views.py                        # Auth endpoints, Team/Match/Training/
│   │                                   # Announcement ViewSets, dashboard summary
│   ├── serializers.py
│   ├── permissions.py                  # IsCoach, IsCoachOrReadOnly, IsOwnerOrReadOnly
│   ├── urls.py                         # Router + custom API Explorer root
│   └── migrations/
│
└── volleyball_project/
    ├── settings.py
    ├── urls.py
    ├── views.py                        # Dashboard, matches, statistics, news,
    │                                   # achievements, notifications, role select
    ├── templates/
    │   ├── base.html                   # Sidebar layout, orange header, badge polling
    │   ├── dashboard.html
    │   ├── matches.html
    │   ├── statistics.html             # Chart.js doughnut, line, radar charts
    │   ├── messages.html
    │   ├── news.html
    │   ├── achievements.html
    │   ├── notifications.html
    │   ├── accounts/
    │   │   ├── login.html
    │   │   ├── register.html
    │   │   ├── profile.html
    │   │   ├── change_password.html
    │   │   ├── role_select.html
    │   │   └── manage_team_members.html
    │   ├── messaging/
    │   │   ├── inbox.html
    │   │   ├── conversation.html
    │   │   └── notifications.html
    │   ├── scheduling/
    │   │   ├── calendar.html
    │   │   ├── schedule_form.html
    │   │   ├── match_detail.html
    │   │   ├── training_detail.html
    │   │   └── payment_status.html
    │   └── rest_framework/
    │       ├── api_root.html           # Custom interactive API Explorer
    │       └── base.html              # Themed DRF browsable API base
    └── static/
        ├── css/volleyball.css          # Blue/orange design system
        └── js/volleyball.js
```

---

## URL Reference

| URL | View | Access |
|---|---|---|
| `/dashboard/` | Dashboard | All users |
| `/matches/` | Match list | All users |
| `/statistics/` | Team statistics | All users |
| `/calendar/` | Monthly calendar | All users |
| `/match/<pk>/` | Match detail | Team members only |
| `/training/<pk>/` | Training detail | Team members only |
| `/schedule/match/` | Create match | Coach only |
| `/schedule/match/<pk>/edit/` | Edit match | Coach only |
| `/schedule/match/<pk>/cancel/` | Cancel match | Coach only (POST) |
| `/schedule/training/` | Create training | Coach only |
| `/schedule/training/<pk>/edit/` | Edit training | Coach only |
| `/schedule/training/<pk>/cancel/` | Cancel training | Coach only (POST) |
| `/payments/` | Payment status | Player / Parent / Manager |
| `/news/` | Team news | All users; post = Coach only |
| `/achievements/` | Achievements | All users; manage = Coach only |
| `/messages/` | Inbox | All users |
| `/notifications/` | Notifications | All users |
| `/profile/` | User profile | All users |
| `/manage-team/` | Manage team members | Coach / Manager |
| `/api/` | API Explorer | Public |
| `/api/auth/login/` | Token login | Public |
| `/api/auth/register/` | Register | Public |
| `/api/auth/me/` | Current user | Authenticated |
| `/api/dashboard/` | Dashboard summary | Authenticated |
| `/api/teams/` | Teams CRUD | Auth; write = Coach |
| `/api/matches/` | Matches CRUD | Auth; write = Coach |
| `/api/trainings/` | Trainings CRUD | Auth; write = Coach |
| `/api/announcements/` | Announcements CRUD | Auth; write = Coach |