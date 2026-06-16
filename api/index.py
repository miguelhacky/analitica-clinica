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
        from core.models import Paciente
        if Paciente.objects.count() == 0:
            fixture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data_fixture.json')
            if os.path.exists(fixture_path):
                call_command('loaddata', fixture_path)
                print("Fixture loaded", flush=True)
        else:
            print(f"Data exists ({Paciente.objects.count()} patients)", flush=True)
    except Exception as e:
        import traceback
        print(f"Setup error: {e}\n{traceback.format_exc()}", flush=True)

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
