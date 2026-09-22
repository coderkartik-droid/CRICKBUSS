import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'crickbuss.settings'
import django; django.setup()

F = open('_diag_out.txt', 'w')

from apps.accounts.models import CustomUser
from django.db.models.fields.files import ImageField
import inspect
src = inspect.getsource(ImageField.check)
F.write(src[:1500] + '\n---\n')
# manually run the PIL check
try:
    from PIL import Image  # noqa: F401
    F.write(f'PIL import OK version {Image.__version__}\n')
    F.write(f'PIL path: {inspect.getfile(Image)}\n')
except Exception as e:
    F.write(f'PIL import FAILED: {type(e).__name__} {e}\n')
from django.core.files.images import get_image_dimensions
F.write('gid func OK\n')
avatar_field = CustomUser._meta.get_field('avatar')
F.write(f'avatar_field type mro: {[c.__name__ for c in type(avatar_field).__mro__]}\n')
try:
    res = avatar_field.check()
    F.write(f'field.check = {res}\n')
except Exception as e:
    F.write(f'field.check crashed: {type(e).__name__} {e}\n')
# test ImageFileDescriptor check
from django.core.checks.model_checks import check_all_models
from django.apps import apps
for m in apps.get_models():
    for f in m._meta.get_fields():
        from django.db.models import ImageField as IF2
        if isinstance(f, IF2):
            try:
                res = f.check()
            except Exception as e:
                res = f'EXC:{e}'
            if res:
                F.write(f'{m.__name__}.{f.name}: {res}\n')
                break
    else:
        continue
    break
F.close()

