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
import json


def send_email_brevo(subject, html_content, to_email):
    if not settings.BREVO_API_KEY:
        from django.core.mail import send_mail
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        send_mail(subject, text, settings.BREVO_SMTP_USER or 'noreply@healthanalytics.com', [to_email], fail_silently=False)
        return
    config = sib_api_v3_sdk.Configuration()
    config.api_key['api-key'] = settings.BREVO_API_KEY
    api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(config))
    sender = {'email': settings.BREVO_SMTP_USER, 'name': 'HealthAnalytics IPS'}
    to = [{'email': to_email}]
    api.send_transac_email(
        sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=to, subject=subject, html_content=html_content)
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'register.html')


def dashboard_view(request):
    return render(request, 'dashboard.html', {
        'user_email': request.user.email if request.user.is_authenticated else '',
        'user_role': request.user.role if request.user.is_authenticated else '',
    })


def pacientes_view(request):
    return render(request, 'pacientes.html', {
        'user_email': request.user.email if request.user.is_authenticated else '',
        'user_role': request.user.role if request.user.is_authenticated else '',
    })


def paciente_editar_view(request, paciente_id=None):
    return render(request, 'paciente_form.html', {
        'user_email': request.user.email if request.user.is_authenticated else '',
        'user_role': request.user.role if request.user.is_authenticated else '',
        'paciente_id': paciente_id,
    })


def etl_view(request):
    return render(request, 'etl.html', {
        'user_email': request.user.email if request.user.is_authenticated else '',
        'user_role': request.user.role if request.user.is_authenticated else '',
    })


def analytics_view(request):
    return render(request, 'analytics.html', {
        'user_email': request.user.email if request.user.is_authenticated else '',
        'user_role': request.user.role if request.user.is_authenticated else '',
    })


def predicciones_view(request):
    return render(request, 'predicciones.html', {
        'user_email': request.user.email if request.user.is_authenticated else '',
        'user_role': request.user.role if request.user.is_authenticated else '',
    })


def reportes_view(request):
    return render(request, 'reportes.html', {
        'user_email': request.user.email if request.user.is_authenticated else '',
        'user_role': request.user.role if request.user.is_authenticated else '',
    })


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


def password_reset_view(request):
    return render(request, 'password_reset.html')


@csrf_exempt
def password_reset_send_code(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email)
            code = ''.join(random.choices(string.digits, k=6))
            PasswordResetCode.objects.create(user=user, code=code)
            send_email_brevo(
                'Código de recuperación - HealthAnalytics IPS',
                f'<h2>Recuperación de contraseña</h2><p>Tu código de recuperación es:</p><h1 style="color:#0c4a6e;letter-spacing:5px">{code}</h1><p>Este código expira al usarlo.</p>',
                email,
            )
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
