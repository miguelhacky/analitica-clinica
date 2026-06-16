import os
import sys
from django.core.wsgi import get_wsgi_application

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_analytics.settings')

if os.environ.get('VERCEL'):
    from django.core.management import call_command
    call_command('vercel_setup')

app = get_wsgi_application()
