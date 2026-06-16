from django.db.models.signals import post_migrate
from django.contrib.auth import get_user_model
from django.dispatch import receiver


@receiver(post_migrate)
def create_admin_user(sender, **kwargs):
    if sender.name != 'accounts':
        return
    User = get_user_model()
    if not User.objects.filter(email='admin@gmail.com').exists():
        User.objects.create_superuser(
            email='admin@gmail.com',
            password='admin1234',
            role='Administrador',
            first_name='Admin',
            last_name='HealthAnalytics',
        )
        print('Usuario administrador creado: admin@gmail.com / admin1234')
