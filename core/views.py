from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
from .models import Paciente, Prediccion
from .serializers import PacienteSerializer, PrediccionSerializer
from etl.etl_processor import run_etl
from etl.dataset_generator import generar_dataset
from etl.models import HistorialETL
from analytics.analytics_engine import calcular_estadisticas, calcular_kpis, segmentar_datos, obtener_tendencias
from analytics.ml_model import predictor
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def get_role(request):
    return request.user.role if request.user.is_authenticated else None


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Administrador'


class IsAdminOrMedico(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['Administrador', 'Medico']


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all().order_by('-fecha_consulta')
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAdminOrMedico()]
        elif self.action in ['destroy']:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Paciente.objects.all().order_by('-fecha_consulta')
        search = self.request.query_params.get('search', None)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(nombres__icontains=search) |
                Q(apellidos__icontains=search) |
                Q(id_paciente__icontains=search) |
                Q(diagnostico_preliminar__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        peso = serializer.validated_data.get('peso', 0)
        altura = serializer.validated_data.get('altura', 1)
        imc = round(peso / (altura ** 2), 1) if altura > 0 else 0
        serializer.save(IMC=imc)

    def perform_update(self, serializer):
        peso = serializer.validated_data.get('peso', 0)
        altura = serializer.validated_data.get('altura', 1)
        imc = round(peso / (altura ** 2), 1) if altura > 0 else 0
        serializer.save(IMC=imc)


class PrediccionViewSet(viewsets.ModelViewSet):
    queryset = Prediccion.objects.all().order_by('-created_at')
    serializer_class = PrediccionSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_etl_view(request):
    source = request.data.get('source', 'dataset')
    user = request.user

    if source == 'file':
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No se envió archivo'}, status=status.HTTP_400_BAD_REQUEST)
        temp_path = f"/tmp/etl_{user.id}_{file.name}"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)
        result = run_etl(temp_path, user)
    else:
        dataset_path = os.path.join(os.path.dirname(__file__), '..', 'media', 'dataset_clinico.xlsx')
        os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
        if not os.path.exists(dataset_path):
            generar_dataset(dataset_path, 1800)
        result = run_etl(dataset_path, user)

    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def train_model_view(request):
    pacientes = Paciente.objects.all()
    if pacientes.count() < 10:
        return Response({'error': 'Se necesitan al menos 10 pacientes'}, status=400)

    success = predictor.train(pacientes, request.data.get('model_type', 'random_forest'))
    if success:
        model_dir = os.path.join(os.path.dirname(__file__), '..', 'media', 'models')
        os.makedirs(model_dir, exist_ok=True)
        predictor.save_model(os.path.join(model_dir, 'clinical_model.joblib'))
        return Response({'message': 'Modelo entrenado', 'metrics': predictor.metrics})
    return Response({'error': 'Error al entrenar'}, status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def predict_all_view(request):
    pacientes = Paciente.objects.all()
    if not pacientes:
        return Response({'error': 'No hay pacientes'}, status=400)

    if predictor.model is None:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'media', 'models', 'clinical_model.joblib')
        try:
            if os.path.exists(model_path):
                predictor.load_model(model_path)
            else:
                success = predictor.train(pacientes)
                if not success:
                    return Response({'error': 'No se pudo entrenar'}, status=500)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    results = []
    for paciente in pacientes:
        pred = predictor.predict(paciente)
        Prediccion.objects.create(
            paciente=paciente,
            riesgo_predicho=pred['riesgo'],
            probabilidad=pred['probabilidad'],
            modelo='Random Forest',
        )
        results.append({
            'paciente_id': paciente.id_paciente,
            'paciente_nombre': f"{paciente.nombres} {paciente.apellidos}",
            'riesgo_predicho': pred['riesgo'],
            'probabilidad': pred['probabilidad'],
        })

    return Response({'message': f'{len(results)} predicciones', 'predictions': results, 'metrics': predictor.metrics})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_kpis(request):
    return Response({
        'kpis': calcular_kpis(),
        'estadisticas': calcular_estadisticas(),
        'segmentos': segmentar_datos(),
        'tendencias': obtener_tendencias(),
        'etl_historial': [
            {
                'fecha': h.fecha.strftime('%Y-%m-%d %H:%M'),
                'estado': h.estado,
                'registros': h.registros_procesados,
                'tiempo': h.tiempo_ejecucion,
            } for h in HistorialETL.objects.order_by('-fecha')[:5]
        ],
        'modelo_metrics': predictor.metrics,
        'user_role': get_role(request),
        'user_email': request.user.email,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reportes_view_api(request):
    tipo = request.GET.get('tipo', 'excel')
    pacientes = Paciente.objects.all().values()
    if not pacientes:
        return Response({'error': 'No hay datos'}, status=404)

    df = pd.DataFrame(list(pacientes))

    if tipo == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Pacientes')
            pd.DataFrame([calcular_kpis()]).to_excel(writer, index=False, sheet_name='KPIs')
            stats_df = pd.DataFrame(calcular_estadisticas()).T.reset_index()
            stats_df.columns = ['Variable', 'Media', 'Mediana', 'Moda', 'Desviacion', 'Min', 'Max']
            stats_df.to_excel(writer, index=False, sheet_name='Estadisticas')
            for key, val in segmentar_datos().items():
                if val:
                    pd.DataFrame(list(val.items()), columns=['Categoria', 'Cantidad']).to_excel(
                        writer, index=False, sheet_name=key.replace('por_', '').capitalize()[:31])
        output.seek(0)
        resp = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename=reporte_healthanalytics.xlsx'
        return resp

    elif tipo == 'csv':
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        resp = HttpResponse(output.read(), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename=reporte_pacientes.csv'
        return resp

    elif tipo == 'pdf':
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), title='Reporte HealthAnalytics IPS')
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph('Reporte HealthAnalytics IPS', styles['Title']))
        elements.append(Spacer(1, 20))
        kpis = calcular_kpis()
        elements.append(Paragraph(
            f"Total: {kpis['total_pacientes']} | Criticos: {kpis['pacientes_criticos']} | "
            f"Hipertensos: {kpis['pacientes_hipertensos']} | Diabeticos: {kpis['pacientes_diabeticos']} | "
            f"Fumadores: {kpis['pacientes_fumadores']}", styles['Normal']))
        elements.append(Spacer(1, 20))
        p_list = list(pacientes[:50])
        if p_list:
            headers = list(p_list[0].keys())
            data = [headers] + [[str(p.get(h, ''))[:30] for h in headers] for p in p_list]
            t = Table(data, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.1, 0.3, 0.6)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        resp = HttpResponse(buffer.read(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename=reporte_healthanalytics.pdf'
        return resp

    return Response({'error': 'Tipo no válido'}, status=400)
