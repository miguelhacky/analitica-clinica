from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pacientes', views.PacienteViewSet)
router.register(r'predicciones', views.PrediccionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('etl/run/', views.run_etl_view, name='etl-run'),
    path('ml/train/', views.train_model_view, name='ml-train'),
    path('ml/predict/', views.predict_all_view, name='ml-predict'),
    path('dashboard/kpis/', views.dashboard_kpis, name='dashboard-kpis'),
    path('reportes/', views.reportes_view_api, name='reportes'),
]
