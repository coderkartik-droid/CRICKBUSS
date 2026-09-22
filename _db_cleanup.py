import os
import sys
from collections import OrderedDict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')

import django
django.setup()

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection, transaction

User = get_user_model()

REPORT = []
DELETED = OrderedDict()

def rpt(s):
    REPORT.append(str(s))
    print(s)

# ===========================================================
# 1) Identify KEEPER superuser: username='admin'
# ===========================================================
rpt("=" * 70)
rpt("DATABASE CLEANUP STARTED")
rpt("=" * 70)

KEEPER = None
sort_field = 'created_at' if hasattr(User, 'created_at') else 'date_joined'
for u in User.objects.filter(is_superuser=True).order_by(sort_field):
    if u.username and u.username.lower() == 'admin':
        KEEPER = u
        break
if not KEEPER:
    for u in User.objects.filter(is_superuser=True).order_by('id'):
        KEEPER = u
        break
assert KEEPER, "FATAL: No superuser found to keep!"

keeper_id = KEEPER.id
rpt(f"KEEPING Superuser: id={KEEPER.id} username={KEEPER.username!r} email={KEEPER.email!r}")
rpt("")

# ===========================================================
# 2) Pre-stage: clear M2M relationships + nullable FKs on Match
#    (best-effort ordering to keep FKs happy before turning off checks)
# ===========================================================
rpt("--- Pre-stage: clearing relationships ---")
try:
    from apps.matches.models import Match
    for m in Match.objects.all():
        try: m.assigned_scorers.clear()
        except Exception: pass
        try: m.officials.clear()
        except Exception: pass
        try: m.sponsors.clear()
        except Exception: pass
        try: m.team1_playing_xi.clear()
        except Exception: pass
        try: m.team2_playing_xi.clear()
        except Exception: pass
        try:
            m.team1_captain = None; m.team1_vice_captain = None
            m.team2_captain = None; m.team2_vice_captain = None
            m.man_of_match = None; m.winning_team = None; m.toss_winner = None
            m.save(update_fields=['team1_captain','team1_vice_captain','team2_captain',
                                  'team2_vice_captain','man_of_match','winning_team','toss_winner'])
        except Exception: pass
except Exception as e:
    rpt(f"  Note Match M2M: {e}")

try:
    from apps.series.models import Series
    for s in Series.objects.all():
        try: s.participating_teams.clear()
        except Exception: pass
except Exception: pass

# ===========================================================
# 3) Bulk-delete user-related data (keeping KEEPER user row)
#    — do this before disabling FKs so the user delete cascade does its job
#    — also wipe related tables explicitly
# ===========================================================
rpt("--- Delete all non-keeper users & all user-linked rows ---")

# Explicitly delete all user-linked tables
try:
    from apps.accounts.models import LoginHistory
    n = LoginHistory.objects.count()
    LoginHistory.objects.all().delete()
    DELETED["LoginHistory"] = n
    rpt(f"  LoginHistory deleted: {n}")
except Exception as e:
    rpt(f"  LoginHistory err: {e}")

try:
    from apps.dashboard.models import SavedMatch, NotificationPreference, SiteSetting
    n = SavedMatch.objects.count()
    SavedMatch.objects.all().delete()
    DELETED["SavedMatch"] = n
    rpt(f"  SavedMatch deleted: {n}")
    n = NotificationPreference.objects.count()
    NotificationPreference.objects.all().delete()
    DELETED["NotificationPreference"] = n
    rpt(f"  NotificationPreference deleted: {n}")
except Exception as e:
    rpt(f"  Dashboard err: {e}")

try:
    from django.contrib.admin.models import LogEntry
    n = LogEntry.objects.count()
    LogEntry.objects.all().delete()
    DELETED["LogEntry (admin logs)"] = n
    rpt(f"  LogEntry deleted: {n}")
except Exception as e:
    rpt(f"  LogEntry err: {e}")

try:
    from django.contrib.sessions.models import Session
    n = Session.objects.count()
    Session.objects.all().delete()
    DELETED["Session (all)"] = n
    rpt(f"  Sessions deleted: {n}")
except Exception as e:
    rpt(f"  Session err: {e}")

# News article FKs to user
try:
    from apps.news.models import ArticleComment, ArticleLike, ArticleBookmark
    for M, name in [(ArticleComment, "ArticleComment"),
                    (ArticleLike, "ArticleLike"),
                    (ArticleBookmark, "ArticleBookmark")]:
        n = M.objects.count()
        M.objects.all().delete()
        DELETED[name] = n
        rpt(f"  {name} deleted: {n}")
except Exception as e:
    rpt(f"  News linked: {e}")

try:
    from apps.videos.models import VideoLike, VideoBookmark
    for M, name in [(VideoLike, "VideoLike"), (VideoBookmark, "VideoBookmark")]:
        n = M.objects.count()
        M.objects.all().delete()
        DELETED[name] = n
        rpt(f"  {name} deleted: {n}")
except Exception as e:
    rpt(f"  Video linked: {e}")

# Delete all users except KEEPER (Cascade will wipe any remaining user-related rows)
other_users = User.objects.exclude(id=keeper_id)
other_count = other_users.count()
rpt(f"  Users to delete: {other_count}")
for u in list(other_users):
    rpt(f"    DELETE user id={u.id} username={u.username!r} email={u.email!r}")
other_users.delete()
DELETED["Users (deleted)"] = other_count
DELETED["Users (kept)"] = 1

KEEPER = User.objects.get(id=keeper_id)
rpt(f"  Remaining users: {User.objects.count()} (expected 1)")

# ===========================================================
# 4) Now turn OFF FK checks for remaining app data,
#    delete every application model we want empty,
#    then turn FK checks back on.
# ===========================================================
rpt("")
rpt("--- Bulk-delete application data (FK checks OFF temporarily) ---")

# The list of models / tables we want completely empty.
APP_MODELS_DELETE = [
    # Matches
    ("matches", ["BallByBall", "FallOfWicket", "Partnership",
                 "PlayerMatchInnings", "BowlerMatchInnings",
                 "Innings", "Match",
                 "Official", "Sponsor", "Ground", "Venue"]),
    # Players / Teams
    ("players", ["BattingStat", "BowlingStat", "Player"]),
    ("teams", ["Team"]),
    # Series / Rankings
    ("series", ["PointsTableEntry", "Series"]),
    ("rankings", ["RankingEntry"]),
    # News / Videos / Photos
    ("news", ["NewsArticle", "NewsCategory"]),
    ("videos", ["CricketVideo", "VideoCategory"]),
    ("photos", ["PhotoItem", "PhotoAlbum"]),
]

with connection.cursor() as cur:
    cur.execute("PRAGMA foreign_keys = OFF")
    rpt("  PRAGMA foreign_keys = OFF")

    try:
        for app_name, model_names in APP_MODELS_DELETE:
            for mname in model_names:
                try:
                    M = apps.get_model(app_name, mname)
                except LookupError:
                    continue
                n = M.objects.count()
                if n > 0:
                    table = M._meta.db_table
                    # Raw DELETE — fastest and avoids FK order in Django
                    cur.execute(f'DELETE FROM "{table}"')
                    DELETED[f"{app_name}.{mname}"] = n
                    rpt(f"  DELETE {app_name}.{mname} [{table}] => {n} rows")
                else:
                    DELETED[f"{app_name}.{mname}"] = 0

        # Also empty any M2M/intermediate tables for these apps
        M2M_TABLES = [
            "matches_match_assigned_scorers",
            "matches_match_officials",
            "matches_match_sponsors",
            "matches_match_team1_playing_xi",
            "matches_match_team2_playing_xi",
            "series_series_participating_teams",
        ]
        for t in M2M_TABLES:
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{t}"')
                n = cur.fetchone()[0]
                if n > 0:
                    cur.execute(f'DELETE FROM "{t}"')
                    DELETED[f"m2m:{t}"] = n
                    rpt(f"  DELETE m2m {t} => {n} rows")
            except Exception:
                pass

        # ===========================================================
        # 5) Reset SQLite autoincrement for ALL tables that had records
        # ===========================================================
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
        if cur.fetchone():
            cur.execute("DELETE FROM sqlite_sequence")
            rpt("  Reset all rows in sqlite_sequence (autoincrement reset)")

        # Re-enable FKs
        cur.execute("PRAGMA foreign_keys = ON")
        rpt("  PRAGMA foreign_keys = ON (re-enabled)")
    except Exception:
        # attempt to re-enable FKs even if we fail
        try: cur.execute("PRAGMA foreign_keys = ON")
        except Exception: pass
        raise

# ===========================================================
# 6) SQLite integrity + FK checks
# ===========================================================
rpt("")
rpt("--- Integrity checks ---")
with connection.cursor() as cur:
    cur.execute("PRAGMA integrity_check")
    rows = cur.fetchall()
    integ_ok = all(r[0] == 'ok' for r in rows)
    rpt(f"  PRAGMA integrity_check : {'OK' if integ_ok else str(rows)}")

    cur.execute("PRAGMA foreign_key_check")
    fk_violations = cur.fetchall()
    fk_ok = len(fk_violations) == 0
    rpt(f"  PRAGMA foreign_key_check: {'OK (0 violations)' if fk_ok else 'FAIL -> ' + str(fk_violations[:5])}")

# ===========================================================
# 7) VALIDATION
# ===========================================================
rpt("")
rpt("=" * 70)
rpt("VALIDATION COUNTS")
rpt("=" * 70)

checks = OrderedDict()
checks["Users (total)"] = (User.objects.count(), 1)
checks["Users (superusers)"] = (User.objects.filter(is_superuser=True).count(), 1)
checks["Users (staff)"] = (User.objects.filter(is_staff=True).count(), 1)

from apps.teams.models import Team
from apps.players.models import Player
from apps.matches.models import Match, Venue, Ground, Innings, BallByBall, PlayerMatchInnings, BowlerMatchInnings, Sponsor
from apps.series.models import Series
from apps.news.models import NewsArticle
from apps.photos.models import PhotoAlbum, PhotoItem
from apps.videos.models import CricketVideo
from apps.accounts.models import LoginHistory
from apps.dashboard.models import SavedMatch, NotificationPreference

checks["Teams"] = (Team.objects.count(), 0)
checks["Players"] = (Player.objects.count(), 0)
checks["Matches"] = (Match.objects.count(), 0)
checks["Venues"] = (Venue.objects.count(), 0)
checks["Grounds"] = (Ground.objects.count(), 0)
checks["Innings"] = (Innings.objects.count(), 0)
checks["Series"] = (Series.objects.count(), 0)
checks["Batting scorecards"] = (PlayerMatchInnings.objects.count(), 0)
checks["Bowling scorecards"] = (BowlerMatchInnings.objects.count(), 0)
checks["Ball events"] = (BallByBall.objects.count(), 0)
checks["News articles"] = (NewsArticle.objects.count(), 0)
checks["Photo albums"] = (PhotoAlbum.objects.count(), 0)
checks["Photo items"] = (PhotoItem.objects.count(), 0)
checks["Videos"] = (CricketVideo.objects.count(), 0)
checks["Sponsors"] = (Sponsor.objects.count(), 0)
checks["LoginHistory"] = (LoginHistory.objects.count(), 0)
checks["SavedMatch"] = (SavedMatch.objects.count(), 0)
checks["NotificationPrefs"] = (NotificationPreference.objects.count(), 0)

rpt(f"{'Check':<30}{'Actual':>10}{'Expected':>10}{'Result':>10}")
rpt("-" * 62)
all_ok = True
for k, (actual, expected) in checks.items():
    ok = actual == expected
    all_ok = all_ok and ok
    rpt(f"{k:<30}{actual:>10}{expected:>10}{'PASS' if ok else 'FAIL':>10}")

# ===========================================================
# 8) Keeper abilities
# ===========================================================
rpt("")
rpt("=" * 70)
rpt("FINAL VERIFICATION — REMAINING SUPERUSER")
rpt("=" * 70)
k = User.objects.get(id=keeper_id)
rpt(f"  User id        : {k.id}")
rpt(f"  username       : {k.username}")
rpt(f"  email          : {k.email}")
rpt(f"  is_superuser   : {k.is_superuser} [requires True for Django Admin]")
rpt(f"  is_staff       : {k.is_staff} [requires True for Django Admin]")
rpt(f"  is_active      : {k.is_active}")
rpt(f"  role           : {getattr(k, 'role', 'N/A')}")
django_admin_ok = k.is_superuser and k.is_staff and k.is_active
rpt(f"  Django Admin login allowed   : {django_admin_ok}")
dashboard_ok = k.is_active and bool(getattr(k, 'role', ''))
rpt(f"  Dashboard login (role+active): {dashboard_ok}")

rpt("")
rpt("=" * 70)
rpt("PER-MODEL DELETIONS SUMMARY")
rpt("=" * 70)
total_del = 0
for k, n in DELETED.items():
    if isinstance(n, int):
        total_del += n if n > 0 else 0
        marker = "  "
        if n > 0: marker = "* "
        rpt(f"  {marker}{k:<45}{n:>8}")
rpt("")
rpt(f"  TOTAL records deleted (approx): {total_del}")

rpt("")
rpt("CLEANUP COMPLETE")

open("_cleanup_report.txt", "w", encoding="utf-8").write("\n".join(REPORT))
print("\nReport saved to _cleanup_report.txt")
sys.exit(0 if (all_ok and integ_ok and fk_ok) else 2)
