```
cd volleyball
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```
# Volleyball Platform — SCRUM-12: Coach Schedules Matches & Training

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply migrations
python manage.py migrate

# 3. Seed demo data (teams, users, matches, trainings)
python manage.py seed_demo

# 4. Run the development server
python manage.py runserver
```

Then open http://127.0.0.1:8000/login/

## Demo Accounts

| Username   | Password    | Role    | Access                          |
|------------|-------------|---------|----------------------------------|
| coach1     | coach123    | Coach   | Full scheduling (create/edit/cancel) |
| player1    | player123   | Player  | View-only calendar & matches     |
| captain1   | captain123  | Captain | View-only                        |

---

## Sprint Deliverables (SCRUM-12)

### Models (`scheduling/models.py`)
- **Team** — team names
- **UserProfile** — role-based user (player/captain/coach/parent/manager)
- **Match** — home vs away team, date, location, status, score
- **TrainingSession** — title, team, date, location, duration, status
- **Announcement** — team announcements shown on dashboard

### Views (`scheduling/views.py`)
| View | URL | Access |
|------|-----|--------|
| `calendar_view` | `/calendar/` | All logged-in users |
| `schedule_match` | `/schedule/match/` | Coach only |
| `schedule_training` | `/schedule/training/` | Coach only |
| `edit_match` | `/schedule/match/<pk>/edit/` | Coach only |
| `edit_training` | `/schedule/training/<pk>/edit/` | Coach only |
| `cancel_match` | `/schedule/match/<pk>/cancel/` | Coach only (POST) |
| `cancel_training` | `/schedule/training/<pk>/cancel/` | Coach only (POST) |
| `calendar_events_api` | `/calendar/api/events/` | All (JSON) |

### Forms (`scheduling/forms.py`)
- **MatchForm** — validates home ≠ away, date must be future
- **TrainingSessionForm** — validates date must be future

### Templates
- `templates/scheduling/calendar.html` — monthly grid + upcoming events sidebar
- `templates/scheduling/schedule_form.html` — shared create/edit form

### Frontend Theme
Blue (`#1e2b8a`) & orange (`#f5a623`) matching the Figma prototype.
Responsive sidebar navigation with active-page highlighting.

---

## Project Structure

```
volleyball/
├── manage.py
├── requirements.txt
├── scheduling/
│   ├── models.py          ← Team, UserProfile, Match, TrainingSession, Announcement
│   ├── views.py           ← All scheduling views + coach_required decorator
│   ├── forms.py           ← MatchForm, TrainingSessionForm with validation
│   ├── urls.py            ← URL patterns for scheduling
│   ├── admin.py           ← Admin registrations
│   ├── apps.py
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── templatetags/
│   │   └── calendar_tags.py   ← has_key, dict_get filters
│   └── management/
│       └── commands/
│           └── seed_demo.py   ← Demo data seeder
└── volleyball_project/
    ├── settings.py
    ├── urls.py
    ├── views.py            ← Dashboard, matches, stats stub views
    ├── templates/
    │   ├── base.html       ← Sidebar layout + orange header
    │   ├── dashboard.html
    │   ├── matches.html
    │   ├── statistics.html
    │   ├── messages.html
    │   ├── news.html
    │   ├── achievements.html
    │   ├── notifications.html
    │   ├── auth/
    │   │   ├── login.html
    │   │   └── role_select.html
    │   └── scheduling/
    │       ├── calendar.html
    │       └── schedule_form.html
    └── static/
        ├── css/volleyball.css
        └── js/volleyball.js
```
