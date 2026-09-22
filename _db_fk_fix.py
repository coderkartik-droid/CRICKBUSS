import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')
import django
django.setup()
from django.db import connection

# Enumerate ALL app-related tables from DB (not just the models) and empty them
# (keeping accounts_customuser with just the single keeper, and auth/django core tables untouched).
KEEP_TABLES_PREFIXES = [
    "django_",          # Django core: migrations, admin_log (log), content types, sessions (we empty later if applicable)
    "auth_",            # auth: permission, group, user_permissions, groups
    "token_blacklist_", # simplejwt
    "accounts_customuser", # keep the user base table (we filter, not empty)
]
# Tables we want to KEEP contents of (never empty)
ABSOLUTE_KEEP = {
    "django_migrations",
    "auth_permission",
    "auth_group",
    "django_content_type",
    "accounts_customuser", # handled separately — we just delete non-keepers
    "django_session",      # keep, will be empty after first run anyway
}

# Tables we explicitly WANT EMPTY and have FKs to user — we just keep the user row
# Also anything in the apps: matches_*, players_*, teams_*, series_*, rankings_*,
# news_*, videos_*, photos_*, dashboard_*, accounts_loginhistory etc.
PURGE_PREFIXES = [
    "matches_",
    "players_",
    "teams_",
    "series_",
    "rankings_",
    "news_",
    "videos_",
    "photos_",
    "dashboard_",
]
# Accounts tables other than customuser
PURGE_TABLES_EXACT = {
    "accounts_loginhistory",
    # user_permissions / groups will be purged via the user deletes cascade
}

with connection.cursor() as cur:
    # List all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [r[0] for r in cur.fetchall()]

    print("ALL TABLES:")
    for t in all_tables: print("  ", t)
    print()

    cur.execute("PRAGMA foreign_keys = OFF")
    print("PRAGMA foreign_keys = OFF")

    # 1) Empties every table matching PURGE_PREFIXES or exact set
    for t in all_tables:
        purge = False
        if t in ABSOLUTE_KEEP:
            purge = False
        elif any(t.startswith(p) for p in PURGE_PREFIXES):
            purge = True
        elif t in PURGE_TABLES_EXACT:
            purge = True
        # Also: admin log
        elif t == "django_admin_log":
            purge = True

        if purge:
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            n = cur.fetchone()[0]
            if n > 0:
                cur.execute(f'DELETE FROM "{t}"')
                print(f"  PURGED {t}: {n} rows")
            else:
                print(f"  SKIP {t}: already empty")

    # 2) Wipe sessions (safe to empty)
    cur.execute("SELECT COUNT(*) FROM django_session")
    n = cur.fetchone()[0]
    if n: cur.execute("DELETE FROM django_session"); print(f"  PURGED django_session: {n}")

    # 3) Reset sequences
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    if cur.fetchone():
        cur.execute("DELETE FROM sqlite_sequence")
        print("  Reset sqlite_sequence")

    # 4) Ensure ONLY 1 user exists (delete all but the 'admin' su)
    cur.execute("SELECT id, username, email, is_superuser FROM accounts_customuser ORDER BY username")
    rows = cur.fetchall()
    print(f"\nUsers before: {len(rows)}")
    keeper = None
    for r in rows:
        if r[1] and r[1].lower() == "admin" and r[3]:
            keeper = r[0]
            break
    if keeper is None:
        for r in rows:
            if r[3]: keeper = r[0]; break
    print(f"Keeper user id: {keeper}")
    for r in rows:
        if r[0] != keeper:
            cur.execute("DELETE FROM accounts_customuser WHERE id = %s", [r[0]])
            print(f"  DELETE user {r[0]} un={r[1]} email={r[2]}")
    # Also clean user_permissions / groups / outstandingtoken for non-keepers
    for fk, t in [("user_id", "accounts_customuser_user_permissions"),
                  ("customuser_id", "accounts_customuser_groups"),
                  ("user_id", "token_blacklist_outstandingtoken")]:
        if t in all_tables:
            cur.execute(f'DELETE FROM "{t}" WHERE {fk} NOT IN (SELECT id FROM accounts_customuser)')
    # And user_permissions for the keeper — remove any custom assigned perms (we'll keep
    # the user super so they always have every perm anyway, but clean orphan rows)
    cur.execute("PRAGMA foreign_keys = ON")
    print("\nPRAGMA foreign_keys = ON")

    # Integrity
    cur.execute("PRAGMA integrity_check")
    print(f"integrity_check: {cur.fetchall()}")
    cur.execute("PRAGMA foreign_key_check")
    violations = cur.fetchall()
    print(f"foreign_key_check violations: {len(violations)}")
    for v in violations[:20]: print(" ", v)

    # Row counts
    print("\nFINAL COUNTS:")
    cur.execute("SELECT COUNT(*) FROM accounts_customuser")
    print(f"  Users: {cur.fetchone()[0]} (expect 1)")
    for t in ["teams_team", "players_player", "matches_match", "matches_venue",
              "matches_ground", "series_series", "matches_playermatchinnings",
              "matches_bowlermatchinnings", "matches_ballbyball",
              "news_newsarticle", "photos_photoalbum", "videos_cricketvideo",
              "matches_sponsor", "accounts_loginhistory"]:
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        print(f"  {t}: {cur.fetchone()[0]} (expect 0)")

print("\nDONE")
