import os
import random
import string
import sib_api_v3_sdk
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from django.conf import settings
from accounts.models import User, PasswordResetCode
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
import json


def send_email_brevo(subject, html_content, to_email):
    import logging
    logger = logging.getLogger(__name__)
    try:
        if not settings.BREVO_API_KEY:
            logger.info(f"Email to {to_email}: {subject}")
            return
        config = sib_api_v3_sdk.Configuration()
        config.api_key['api-key'] = settings.BREVO_API_KEY
        api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(config))
        sender = {'email': settings.BREVO_SMTP_USER, 'name': 'HealthAnalytics IPS'}
        to = [{'email': to_email}]
        api.send_transac_email(
            sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)
        )
    except Exception as e:
        logger.error(f"Error sending email: {e}")


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'register.html')


def _user_context(request):
    if request.user.is_authenticated:
        return {
            'user_email': request.user.email,
            'user_role': request.user.role,
            'user_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
            'user_first_name': request.user.first_name,
            'user_profile_pic': request.user.profile_picture.url if request.user.profile_picture else None,
        }
    return {}


def dashboard_view(request):
    return render(request, 'dashboard.html', _user_context(request))


def pacientes_view(request):
    return render(request, 'pacientes.html', _user_context(request))


def paciente_editar_view(request, paciente_id=None):
    ctx = _user_context(request)
    ctx['paciente_id'] = paciente_id
    return render(request, 'paciente_form.html', ctx)


def etl_view(request):
    return render(request, 'etl.html', _user_context(request))


def analytics_view(request):
    return render(request, 'analytics.html', _user_context(request))


def predicciones_view(request):
    return render(request, 'predicciones.html', _user_context(request))


def reportes_view(request):
    return render(request, 'reportes.html', _user_context(request))


@csrf_exempt
def session_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                login(request, user)
                return JsonResponse({'success': True, 'email': user.email, 'role': user.role})
            return JsonResponse({'success': False, 'error': 'Contraseña incorrecta'}, status=401)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Correo incorrecto'}, status=401)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def session_logout(request):
    logout(request)
    return JsonResponse({'success': True})


def csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})


def profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method == 'GET':
        user = request.user
        return JsonResponse({
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
        })
    if request.method == 'POST':
        user = request.user
        data = request.POST
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'date_of_birth' in data and data['date_of_birth']:
            from datetime import datetime
            user.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']
        user.save()
        return JsonResponse({'success': True, 'message': 'Perfil actualizado'})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def password_reset_view(request):
    return render(request, 'password_reset.html')


@csrf_exempt
def password_reset_send_code(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email)
            # Invalidar códigos anteriores no usados
            PasswordResetCode.objects.filter(user=user, used=False).delete()
            code = ''.join(random.choices(string.digits, k=6))
            PasswordResetCode.objects.create(user=user, code=code)
            import threading
            t = threading.Thread(target=send_email_brevo, args=(
                'Código de recuperación - HealthAnalytics IPS',
                f'<h2>Recuperación de contraseña</h2><p>Tu código de recuperación es:</p><h1 style="color:#0c4a6e;letter-spacing:5px">{code}</h1><p>Este código expira al usarlo.</p>',
                email,
            ))
            t.start()
            return JsonResponse({'success': True, 'message': 'Código enviado a tu correo'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No existe una cuenta con ese correo'}, status=404)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def password_reset_verify_view(request):
    return render(request, 'password_reset_verify.html')


@csrf_exempt
def password_reset_verify_code(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        try:
            user = User.objects.get(email=email)
            reset_code = PasswordResetCode.objects.filter(user=user, code=code, used=False).latest('created_at')
            return JsonResponse({'success': True, 'message': 'Código válido'})
        except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Código inválido o expirado'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def password_reset_confirm_view(request):
    email = request.GET.get('email', '')
    code = request.GET.get('code', '')
    return render(request, 'password_reset_confirm.html', {'email': email, 'code': code})


@csrf_exempt
def password_reset_change(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        password1 = data.get('password1', '')
        password2 = data.get('password2', '')
        if password1 != password2:
            return JsonResponse({'success': False, 'error': 'Las contraseñas no coinciden'}, status=400)
        if len(password1) < 6:
            return JsonResponse({'success': False, 'error': 'La contraseña debe tener al menos 6 caracteres'}, status=400)
        try:
            user = User.objects.get(email=email)
            reset_code = PasswordResetCode.objects.filter(user=user, code=code, used=False).latest('created_at')
            user.set_password(password1)
            user.save()
            reset_code.used = True
            reset_code.save()
            return JsonResponse({'success': True, 'message': 'Contraseña actualizada correctamente'})
        except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Código inválido o expirado'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def setup_database(request):
    from django.core.management import call_command
    import io
    output = io.StringIO()
    steps = []
    try:
        call_command('migrate', '--noinput', stdout=output)
        steps.append("Migrate OK")
        if not User.objects.filter(email='admin@gmail.com').exists():
            User.objects.create_superuser(
                email='admin@gmail.com', password='admin1234',
                first_name='Admin', last_name='Principal', role='Administrador'
            )
            steps.append("Admin created")
        else:
            steps.append("Admin exists")
        from core.models import Paciente
        if Paciente.objects.count() == 0:
            fixture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data_fixture.json')
            if os.path.exists(fixture_path):
                call_command('loaddata', fixture_path, stdout=output)
                steps.append("Fixture loaded")
            else:
                steps.append(f"Fixture not found at {fixture_path}")
        else:
            steps.append(f"Data exists ({Paciente.objects.count()} patients)")
        return JsonResponse({'success': True, 'steps': steps})
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e), 'traceback': traceback.format_exc(), 'steps': steps})
