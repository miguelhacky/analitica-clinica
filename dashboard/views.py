from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json


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
    return render(request, 'etl.html')


def analytics_view(request):
    return render(request, 'analytics.html')


def predicciones_view(request):
    return render(request, 'predicciones.html')


def reportes_view(request):
    return render(request, 'reportes.html')


@csrf_exempt
def session_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = authenticate(request, email=data.get('email'), password=data.get('password'))
        if user:
            login(request, user)
            return JsonResponse({'success': True, 'email': user.email, 'role': user.role})
        return JsonResponse({'success': False, 'error': 'Credenciales inválidas'}, status=401)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def session_logout(request):
    logout(request)
    return JsonResponse({'success': True})


def csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})
