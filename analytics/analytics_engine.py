import pandas as pd
import numpy as np
from django.db.models import Count
from core.models import Paciente, ContagiousDisease


def calcular_estadisticas():
    pacientes = Paciente.objects.all()
    if not pacientes:
        return {}

    df = pd.DataFrame(list(pacientes.values()))

    stats = {}

    numeric_cols = ['edad', 'peso', 'altura', 'IMC', 'presion_sistolica',
                    'presion_diastolica', 'frecuencia_cardiaca', 'glucosa',
                    'colesterol', 'saturacion_oxigeno', 'temperatura']

    for col in numeric_cols:
        if col in df.columns:
            values = df[col].dropna()
            if len(values) > 0:
                stats[col] = {
                    'media': round(float(values.mean()), 2),
                    'mediana': round(float(values.median()), 2),
                    'moda': round(float(values.mode().iloc[0]), 2) if len(values.mode()) > 0 else 0,
                    'desviacion': round(float(values.std()), 2),
                    'min': float(values.min()),
                    'max': float(values.max()),
                }
            else:
                stats[col] = {'media': 0, 'mediana': 0, 'moda': 0, 'desviacion': 0, 'min': 0, 'max': 0}
        else:
            stats[col] = {'media': 0, 'mediana': 0, 'moda': 0, 'desviacion': 0, 'min': 0, 'max': 0}

    return stats


def calcular_kpis():
    total = Paciente.objects.count()
    if total == 0:
        return {
            'total_pacientes': 0,
            'pacientes_criticos': 0,
            'pacientes_hipertensos': 0,
            'pacientes_diabeticos': 0,
            'pacientes_fumadores': 0,
            'riesgo_promedio': 0,
            'pacientes_contagiosos': 0,
            'porcentaje_contagiosos': 0,
            'enfermedades_contagiosas_stats': {},
        }

    criticos = Paciente.objects.filter(riesgo_enfermedad='Crítico').count()
    hipertensos = Paciente.objects.filter(
        presion_sistolica__gte=140
    ).count()
    diabeticos = Paciente.objects.filter(glucosa__gte=126).count()
    fumadores = Paciente.objects.filter(fumador='Sí').count()

    riesgo_map = {'Bajo': 1, 'Medio': 2, 'Alto': 3, 'Crítico': 4}
    riesgos = Paciente.objects.values_list('riesgo_enfermedad', flat=True)
    riesgo_prom = 0
    if riesgos:
        riesgo_nums = [riesgo_map.get(r, 0) for r in riesgos]
        riesgo_prom = round(float(np.mean(riesgo_nums)), 2)

    from django.db.models import Count as _Count
    contagiosos = Paciente.objects.annotate(num_enf=_Count('enfermedades_contagiosas')).filter(num_enf__gt=0).count()
    enf_stats = {}
    for enf in ContagiousDisease.objects.annotate(total_pacientes=_Count('paciente')).filter(total_pacientes__gt=0):
        enf_stats[enf.nombre] = {'total': enf.total_pacientes, 'porcentaje': round(enf.total_pacientes / total * 100, 1)}

    activos = Paciente.objects.filter(estado='Activo').count()
    hospitalizados = Paciente.objects.filter(estado='Hospitalizado').count()
    dados_alta = Paciente.objects.filter(estado='Dado de Alta').count()
    fallecidos = Paciente.objects.filter(estado='Fallecido').count()

    criticos_contagiosos = Paciente.objects.filter(
        riesgo_enfermedad='Crítico'
    ).annotate(num_enf=_Count('enfermedades_contagiosas')).filter(num_enf__gt=0).count()

    return {
        'total_pacientes': total,
        'pacientes_criticos': criticos,
        'pacientes_hipertensos': hipertensos,
        'pacientes_diabeticos': diabeticos,
        'pacientes_fumadores': fumadores,
        'riesgo_promedio': riesgo_prom,
        'porcentaje_criticos': round(criticos / total * 100, 1) if total else 0,
        'porcentaje_hipertensos': round(hipertensos / total * 100, 1) if total else 0,
        'porcentaje_diabeticos': round(diabeticos / total * 100, 1) if total else 0,
        'porcentaje_fumadores': round(fumadores / total * 100, 1) if total else 0,
        'pacientes_contagiosos': contagiosos,
        'porcentaje_contagiosos': round(contagiosos / total * 100, 1) if total else 0,
        'enfermedades_contagiosas_stats': enf_stats,
        'pacientes_activos': activos,
        'pacientes_hospitalizados': hospitalizados,
        'pacientes_dados_alta': dados_alta,
        'pacientes_fallecidos': fallecidos,
        'porcentaje_activos': round(activos / total * 100, 1) if total else 0,
        'porcentaje_hospitalizados': round(hospitalizados / total * 100, 1) if total else 0,
        'porcentaje_dados_alta': round(dados_alta / total * 100, 1) if total else 0,
        'porcentaje_fallecidos': round(fallecidos / total * 100, 1) if total else 0,
        'criticos_contagiosos': criticos_contagiosos,
    }


def segmentar_datos():
    pacientes = Paciente.objects.all()
    if not pacientes:
        return {}

    df = pd.DataFrame(list(pacientes.values()))

    segmentos = {}

    segmentos['por_edad'] = {}
    if 'edad' in df.columns:
        bins = [0, 18, 30, 45, 60, 80, 150]
        labels = ['0-18', '19-30', '31-45', '46-60', '61-80', '80+']
        df['grupo_edad'] = pd.cut(df['edad'], bins=bins, labels=labels, right=False)
        segmentos['por_edad'] = df['grupo_edad'].value_counts().to_dict()
        segmentos['por_edad'] = {str(k): int(v) for k, v in segmentos['por_edad'].items()}

    segmentos['por_sexo'] = {}
    if 'sexo' in df.columns:
        segmentos['por_sexo'] = df['sexo'].value_counts().to_dict()
        segmentos['por_sexo'] = {str(k): int(v) for k, v in segmentos['por_sexo'].items()}

    segmentos['por_riesgo'] = {}
    if 'riesgo_enfermedad' in df.columns:
        segmentos['por_riesgo'] = df['riesgo_enfermedad'].value_counts().to_dict()
        segmentos['por_riesgo'] = {str(k): int(v) for k, v in segmentos['por_riesgo'].items()}

    segmentos['por_diagnostico'] = {}
    if 'diagnostico_preliminar' in df.columns:
        segmentos['por_diagnostico'] = df['diagnostico_preliminar'].value_counts().head(10).to_dict()
        segmentos['por_diagnostico'] = {str(k): int(v) for k, v in segmentos['por_diagnostico'].items()}

    segmentos['por_imc'] = {}
    if 'IMC' in df.columns:
        bins_imc = [0, 18.5, 24.9, 29.9, 40, 100]
        labels_imc = ['Bajo peso', 'Normal', 'Sobrepeso', 'Obesidad', 'Obesidad extrema']
        df['grupo_imc'] = pd.cut(df['IMC'], bins=bins_imc, labels=labels_imc, right=False)
        segmentos['por_imc'] = df['grupo_imc'].value_counts().to_dict()
        segmentos['por_imc'] = {str(k): int(v) for k, v in segmentos['por_imc'].items()}

    return segmentos


def obtener_tendencias():
    pacientes = Paciente.objects.all().order_by('fecha_consulta')
    if not pacientes:
        return {}

    df = pd.DataFrame(list(pacientes.values('fecha_consulta', 'riesgo_enfermedad', 'glucosa', 'colesterol', 'presion_sistolica')))

    if df.empty:
        return {}

    df['fecha_consulta'] = pd.to_datetime(df['fecha_consulta'], errors='coerce')
    df = df.dropna(subset=['fecha_consulta'])
    if df.empty:
        return {}
    df['mes'] = df['fecha_consulta'].dt.to_period('M').astype(str)

    tendencias = {}

    glucosa_trend = df.groupby('mes')['glucosa'].mean().to_dict()
    tendencias['glucosa'] = {str(k): round(float(v), 1) for k, v in glucosa_trend.items()}

    colesterol_trend = df.groupby('mes')['colesterol'].mean().to_dict()
    tendencias['colesterol'] = {str(k): round(float(v), 1) for k, v in colesterol_trend.items()}

    presion_trend = df.groupby('mes')['presion_sistolica'].mean().to_dict()
    tendencias['presion_sistolica'] = {str(k): round(float(v), 1) for k, v in presion_trend.items()}

    riesgo_por_mes = df.groupby(['mes', 'riesgo_enfermedad']).size().unstack(fill_value=0)
    tendencias['riesgo'] = {}
    for col in riesgo_por_mes.columns:
        tendencias['riesgo'][str(col)] = {str(k): int(v) for k, v in riesgo_por_mes[col].to_dict().items()}

    return tendencias
