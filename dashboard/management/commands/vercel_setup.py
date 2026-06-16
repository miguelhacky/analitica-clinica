import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup database: migrate + create admin user'

    def handle(self, *args, **options):
        try:
            call_command('migrate', '--noinput')
            if not User.objects.filter(email='admin@gmail.com').exists():
                User.objects.create_superuser(
                    email='admin@gmail.com',
                    password='admin1234',
                    first_name='Admin',
                    last_name='Principal',
                    role='admin'
                )
                self.stdout.write(self.style.SUCCESS('Admin user created'))
            else:
                self.stdout.write('Admin user already exists')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Setup error: {e}'))
