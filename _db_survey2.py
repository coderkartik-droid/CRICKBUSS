import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')
import django
django.setup()

from django.apps import apps
from django.contrib.auth import get_user_model
User = get_user_model()

lines = []
def wr(s):
    lines.append(str(s))
    print(s)

wr("=== USERS ===")
for u in User.objects.all().order_by('-is_superuser', 'id'):
    roles = []
    if u.is_superuser: roles.append("SU")
    if u.is_staff: roles.append("STAFF")
    r = getattr(u, 'role', '')
    if r: roles.append("role:"+r)
    wr(f"  U id={u.id} un={u.username!r} email={u.email!r} active={u.is_active} {' '.join(roles)}")

wr("=== MODEL COUNTS ===")
for model in apps.get_models():
    try:
        n = model.objects.count()
    except Exception as e:
        n = f"ERR:{e}"
    wr(f"{model.__module__}|{model.__name__}|{model._meta.db_table}|{n}")

open("_db_before_cleanup.txt","w",encoding="utf-8").write("\n".join(lines))
wr("DONE - wrote _db_before_cleanup.txt")
