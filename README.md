# CrickScore Live - Production-Ready Cricket Live Score Web Application

A production-grade, full-stack live cricket scoring web platform inspired by modern sports portals, engineered with clean architecture, real-time WebSockets, REST APIs, and a modern responsive interface.

---

## 🚀 Key Features

### 1. Live Match Engine & Real-Time Scores
- **Live Scoreboard**: Real-time run rates, required run rates, boundaries, and current overs.
- **WebSocket Streaming**: Built on Django Channels for sub-second ball-by-ball score and commentary broadcasts, with automatic fallback to AJAX polling (every 10 seconds).
- **Comprehensive Scorecards**: Detailed innings breakdown, dismissal methods, runs, balls, 4s, 6s, strike rates, bowling figures (overs, maidens, runs, wickets, economy).
- **Data Visualizations**: Interactive Worm Graph (cumulative run comparisons) and Run Rate charts using Chart.js.
- **Match Dynamics**: Partnerships, Fall of Wickets timeline, toss results, pitch & weather reports, umpires, and head-to-head records.

### 2. Tournaments & Series Hub
- Categorized coverage: International Bilateral Tours, ICC Tournaments, IPL, PSL, BBL, BPL, CPL, SA20, ILT20, The Hundred, Women’s Cricket, and Under-19.
- Dynamic Points Tables with automatic Net Run Rate (NRR) ordering and recent form indicators.
- Squad rosters and full fixture schedules.

### 3. Teams & Player Profiles
- Country, franchise, and domestic team homepages with captains, coaches, trophies, home venues, and match histories.
- Deep player career statistics across Test, ODI, T20I, and IPL formats.
- Visual career progression charts and player milestones.

### 4. ICC Rankings
- Test, ODI, and T20I official rankings for both Men and Women.
- Filterable by Batters, Bowlers, All-rounders, and Team Standings, including rank movement trends.

### 5. News & Multimedia
- Breaking news alerts, trending stories, post-match analysis, and editorial features.
- Discussion boards with nested user comments and AJAX likes/bookmarks.
- Video highlight hub with duration badges and embedded streaming.
- High-resolution match action photo albums with lightbox modal view.

### 6. Security & User Accounts
- Role-Based Access Control (Admin, Editor, Moderator, Registered User, Guest).
- Email & Username authentication with 6-digit OTP verification (10-minute expiry).
- Password recovery and reset tokens.
- JWT Authentication (`/api/v1/auth/`) for API clients alongside secure session cookies.
- User Dashboard to manage notification preferences, comment logs, and saved match watchlists.
- Dark / Light Mode with seamless CSS variables and LocalStorage persistence.

---

## 🛠 Technology Stack

- **Backend**: Python 3.13, Django 5.1+, Django REST Framework, Django Channels, Daphne, Celery, Redis.
- **Database**: PostgreSQL (production-ready) / SQLite (development default).
- **Frontend**: HTML5, CSS3 (Modern Emerald & Slate palette), Bootstrap 5, JavaScript (ES6+), FontAwesome 6, Chart.js.
- **Production Server**: Daphne (ASGI for WebSockets), Gunicorn (WSGI), WhiteNoise (static files).

---

## 📂 Project Structure

```
CRICKBUSS/
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # Documentation & setup guide
├── crickbuss/                  # Project configuration
│   ├── __init__.py
│   ├── settings.py             # Base & production settings
│   ├── urls.py                 # Primary URL router
│   ├── asgi.py                 # ASGI & Channels protocol router
│   ├── wsgi.py                 # WSGI application
│   └── celery.py               # Celery task broker setup
├── apps/                       # Modular clean applications
│   ├── accounts/               # User auth, roles, OTP, profile, JWT
│   ├── matches/                # Live score engine, ball-by-ball, commentary
│   ├── teams/                  # Teams, squads, and franchise stats
│   ├── players/                # Profiles, batting & bowling career records
│   ├── series/                 # Tournaments, schedules, points table
│   ├── rankings/               # ICC official rankings
│   ├── news/                   # Articles, categories, comments, likes
│   ├── videos/                 # Video highlights & streaming
│   ├── photos/                 # Photo galleries & lightbox albums
│   ├── dashboard/              # User bookmarks, watchlist, notification settings
│   └── api/                    # Unified REST APIs v1
├── static/                     # CSS, JS, and brand graphics
│   ├── css/style.css           # Custom theme styles
│   ├── css/dark-mode.css       # Dark mode theme overrides
│   ├── js/main.js              # CSRF, AJAX toasts, bookmarks
│   ├── js/live-score.js        # WebSocket / Polling live score engine
│   ├── js/charts.js            # Chart.js graphs
│   └── js/dark-mode.js         # Theme toggle & local persistence
└── templates/                  # Reusable HTML5 templates
    ├── base.html
    ├── navbar.html
    ├── footer.html
    ├── pages/                  # Home, search, about, contact, legal
    ├── matches/                # Live center & scorecards
    ├── teams/                  # Team directory & team home
    ├── players/                # Player list & player profile
    ├── series/                 # Tournaments & points tables
    ├── rankings/               # ICC rankings
    ├── news/                   # News lists & reading view
    ├── videos/                 # Video streaming gallery
    ├── photos/                 # Photo albums
    ├── dashboard/              # User dashboard & settings
    └── accounts/               # Auth, login, register, OTP
```

---

## ⚡ Quick Start Installation Guide

### 1. Prerequisites
- Python 3.10+ (tested with Python 3.13)
- Pip
- Redis (optional for development, recommended for WebSockets & Celery)

### 2. Clone / Open the Project
```bash
cd c:\Users\hari1\CRICKBUSS
```

### 3. Install Dependencies
```bash
py -3.13 -m pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```

### 5. Apply Database Migrations
```bash
py -3.13 manage.py makemigrations
py -3.13 manage.py migrate
```

### 6. Populate Realistic Cricket Sample Data
Run the built-in seeding command:
```bash
py -3.13 manage.py seed_cricket_data
```

This immediately creates:
- **Admin User**: `admin@crickscore.local` / Password: `admin1234`
- **Editor User**: `editor@crickscore.local` / Password: `editor1234`
- **Fan User**: `fan@crickscore.local` / Password: `fan12345`
- International and IPL teams (India, Australia, CSK, MI, England).
- Star player profiles (Virat Kohli, Rohit Sharma, Jasprit Bumrah, Pat Cummins) with career stats.
- Tournaments (IPL 2026, Australia Tour of India) with points tables.
- A **LIVE match in progress** with live score, overs, crease batters, and commentary.
- Breaking news stories, match video highlights, and ICC rankings.

### 7. Run the Development Server
```bash
py -3.13 manage.py runserver
```

Open your browser at:
- Web App: `http://127.0.0.1:8000/`
- Django Admin Portal: `http://127.0.0.1:8000/admin/`
- REST APIs: `http://127.0.0.1:8000/api/v1/`

---

## 🌐 REST API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register/` | Register new user |
| `POST` | `/api/v1/auth/login/` | Obtain JWT access and refresh tokens |
| `GET` | `/api/v1/auth/profile/` | Fetch authenticated user profile |
| `GET` | `/api/v1/matches/` | List all fixtures & results |
| `GET` | `/api/v1/matches/live/now/` | Fetch all currently active live matches |
| `GET` | `/api/v1/matches/<slug>/` | Complete match details & scorecards |
| `GET` | `/api/v1/teams/` | List teams across international & leagues |
| `GET` | `/api/v1/players/` | List players and filter by role |
| `GET` | `/api/v1/series/` | List tournament series & standings |
| `GET` | `/api/v1/rankings/` | Query ICC rankings by gender & format |
| `GET` | `/api/v1/news/` | Fetch editorial cricket news |
| `GET` | `/api/v1/videos/` | Fetch video highlight clips |
| `GET` | `/api/v1/search/?q=<query>` | Global search across all models |

---

## 🚀 Production Deployment Notes

### 1. Daphne & ASGI Setup
Run the ASGI server via Daphne for concurrent WebSocket handling:
```bash
daphne -b 0.0.0.0 -p 8000 crickbuss.asgi:application
```

### 2. Celery Worker (Background tasks & live scoring sync)
```bash
celery -A crickbuss worker -l info
```

### 3. Static Files
```bash
py -3.13 manage.py collectstatic --noinput
```
WhiteNoise serves static files directly with cache headers and gzip compression enabled.
