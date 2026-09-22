import os, sys, traceback
BASE = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, BASE)
os.environ['DJANGO_SETTINGS_MODULE'] = 'crickbuss.settings'
import django
django.setup()
sys.stdout = open('_qa_play_out.log','w',encoding='utf-8')
sys.stderr = sys.stdout
try:
    exec(open(os.path.join(BASE, '_qa_play.py'), encoding='utf-8').read().replace(
        "BASE = os.path.dirname(os.path.abspath(__file__))",
        f"BASE = r'{BASE}'",
    ))
except Exception as e:
    traceback.print_exc()
finally:
    sys.stdout.close()
