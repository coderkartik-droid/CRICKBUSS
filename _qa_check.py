from django.test import Client
from apps.accounts.models import CustomUser

u = CustomUser.objects.filter(is_superuser=True).first()
c = Client()
c.force_login(u)
for p in [
    "/dashboard/local/venue/",
    "/dashboard/local/series/",
    "/dashboard/local/news/",
    "/dashboard/local/match/",
    "/dashboard/local/ground/",
]:
    print(p, c.get(p).status_code)
