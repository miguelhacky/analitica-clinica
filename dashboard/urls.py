from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('pacientes/', views.pacientes_view, name='pacientes'),
    path('pacientes/nuevo/', views.paciente_editar_view, name='paciente-nuevo'),
    path('pacientes/<int:paciente_id>/editar/', views.paciente_editar_view, name='paciente-editar'),
    path('etl/', views.etl_view, name='etl'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('predicciones/', views.predicciones_view, name='predicciones'),
    path('reportes/', views.reportes_view, name='reportes'),
    path('api/auth/session-login/', views.session_login, name='session-login'),
    path('api/auth/session-logout/', views.session_logout, name='session-logout'),
    path('api/auth/csrf/', views.csrf_token, name='csrf-token'),
    path('password-reset/', views.password_reset_view, name='password-reset'),
    path('api/auth/password-reset/send-code/', views.password_reset_send_code, name='password-reset-send-code'),
    path('password-reset/verify/', views.password_reset_verify_view, name='password-reset-verify'),
    path('api/auth/password-reset/verify-code/', views.password_reset_verify_code, name='password-reset-verify-code'),
    path('password-reset/confirm/', views.password_reset_confirm_view, name='password-reset-confirm'),
    path('api/auth/password-reset/change/', views.password_reset_change, name='password-reset-change'),
    path('api/auth/profile/', views.profile_view, name='profile'),
    path('api/setup/', views.setup_database, name='setup-database'),
    path('api/test-email/', views.test_email, name='test-email'),
]
