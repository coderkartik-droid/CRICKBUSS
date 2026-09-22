import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')
django.setup()

from django.apps import apps
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("USERS IN DATABASE")
print("=" * 60)
for u in User.objects.all():
    roles = []
    if u.is_superuser:
        roles.append("SUPERUSER")
    if u.is_staff:
        roles.append("STAFF")
    role = getattr(u, 'role', 'N/A')
    if role:
        roles.append(f"role={role}")
    print(f"  User ID={u.id} username={u.username!r} email={u.email!r} is_active={u.is_active} [{', '.join(roles)}]")

print()
print("=" * 60)
print("ALL MODELS WITH RECORD COUNTS (>0 only)")
print("=" * 60)

counts = []
for model in apps.get_models():
    try:
        n = model.objects.count()
    except Exception as e:
        n = f"ERR: {e}"
    counts.append((model.__module__, model.__name__, model._meta.db_table, n))

# Filter to ones with actual records (exclude 0 counts for readability)
for mod, name, table, n in counts:
    if isinstance(n, int) and n > 0:
        print(f"  [{mod}] {name} (table={table}) -> {n} records")

print()
print("=" * 60)
print("MODELS WITH ZERO RECORDS (sample / confirmation)")
print("=" * 60)
zero_count = 0
for mod, name, table, n in counts:
    if isinstance(n, int) and n == 0:
        zero_count += 1
print(f"  {zero_count} models with 0 records")

with open("_db_before_cleanup.txt", "w", encoding="utf-8") as f:
    for mod, name, table, n in counts:
        f.write(f"{mod}|{name}|{table}|{n}\n")
