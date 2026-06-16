import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_analytics.settings')

import django
django.setup()

if os.environ.get('VERCEL'):
    try:
        from django.core.management import call_command
        call_command('migrate', '--noinput')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(email='admin@gmail.com').exists():
            User.objects.create_superuser(
                email='admin@gmail.com', password='admin1234',
                first_name='Admin', last_name='Principal', role='Administrador'
            )
            print("Admin created", flush=True)
        else:
            print("Admin exists", flush=True)
    except Exception as e:
        print(f"Setup error: {e}", flush=True)

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
