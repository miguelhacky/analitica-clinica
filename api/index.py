import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_analytics.settings')

print("=== STARTUP BEGIN ===", flush=True)
import django
django.setup()
print("django.setup() OK", flush=True)

if os.environ.get('VERCEL'):
    print("VERCEL detected, running setup...", flush=True)
    try:
        from django.core.management import call_command
        print("Running migrate...", flush=True)
        call_command('migrate', '--noinput')
        print("Migrate OK", flush=True)

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
        count_before = Paciente.objects.count()
        print(f"Paciente count before loaddata: {count_before}", flush=True)
        if count_before == 0:
            fixture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data_fixture.json')
            print(f"Fixture path: {fixture_path}", flush=True)
            print(f"Fixture exists: {os.path.exists(fixture_path)}", flush=True)
            if os.path.exists(fixture_path):
                print(f"Fixture size: {os.path.getsize(fixture_path)}", flush=True)
                try:
                    call_command('loaddata', fixture_path, verbosity=3)
                    print("Fixture loaded successfully", flush=True)
                except Exception as load_err:
                    print(f"loaddata error: {load_err}", flush=True)
                    import traceback
                    traceback.print_exc()
        count_after = Paciente.objects.count()
        print(f"Paciente count after loaddata: {count_after}", flush=True)
    except Exception as e:
        print(f"Setup error: {e}", flush=True)
        import traceback
        traceback.print_exc()
else:
    print("Not VERCEL, skipping setup", flush=True)

print("=== STARTUP END ===", flush=True)

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
