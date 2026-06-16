import os
import sys
from django.core.wsgi import get_wsgi_application

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_analytics.settings')

if os.environ.get('VERCEL'):
    from django.core.management import call_command
    
    # Debug: log available DB-related env vars
    for key in sorted(os.environ.keys()):
        if 'DATABASE' in key.upper() or 'POSTGRES' in key.upper() or key in ('DATABASE_URL',):
            val = os.environ.get(key, '')
            print(f"ENV {key}={val[:50]}{'...' if len(val) > 50 else ''}", flush=True)
    
    call_command('vercel_setup')

app = get_wsgi_application()
