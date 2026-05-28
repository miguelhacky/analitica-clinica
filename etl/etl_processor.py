import pandas as pd
import numpy as np
import time
from datetime import datetime
from django.db import transaction
from core.models import Paciente
from .models import HistorialETL


def extract(file_path):
    ext = file_path.lower().split('.')[-1]
    if ext == 'csv':
        df = pd.read_csv(file_path, encoding='utf-8')
    elif ext in ['xlsx', 'xls']:
        df = pd.read_excel(file_path, engine='openpyxl')
    else:
        raise ValueError(f"Formato no soportado: {ext}")

    logs = [
        f"EXTRACT: Archivo cargado: {file_path}",
        f"EXTRACT: Registros iniciales: {len(df)}",
        f"EXTRACT: Columnas: {list(df.columns)}",
        f"EXTRACT: Tipos de datos: {dict(df.dtypes)}",
    ]
    return df, logs


def transform(df):
    logs = []
    original_len = len(df)

    nulls_original = df.isnull().sum().sum()
    logs.append(f"ANTES: {original_len} registros, {nulls_original} valores nulos")

    column_map = {
        'presión_sistólica': 'presion_sistolica',
        'presión_diastólica': 'presion_diastolica',
        'saturación_oxígeno': 'saturacion_oxigeno',
        'actividad_física': 'actividad_fisica',
        'diagnóstico_preliminar': 'diagnostico_preliminar',
        'antecedentes_familiares': 'antecedentes_familiares',
        'riesgo_enfermedad': 'riesgo_enfermedad',
        'frecuencia_cardiaca': 'frecuencia_cardiaca',
        'consumo_alcohol': 'consumo_alcohol',
        'id_paciente': 'id_paciente',
    }
    df.rename(columns=column_map, inplace=True)

    expected_cols = ['id_paciente', 'nombres', 'apellidos', 'edad', 'sexo', 'peso', 'altura',
                     'IMC', 'presion_sistolica', 'presion_diastolica', 'frecuencia_cardiaca',
                     'glucosa', 'colesterol', 'saturacion_oxigeno', 'temperatura',
                     'antecedentes_familiares', 'fumador', 'consumo_alcohol', 'actividad_fisica',
                     'diagnostico_preliminar', 'riesgo_enfermedad', 'fecha_consulta']

    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    df = df[[c for c in expected_cols if c in df.columns] + [c for c in df.columns if c not in expected_cols]]

    before_dedup = len(df)
    df.drop_duplicates(subset=['id_paciente', 'fecha_consulta'], keep='first', inplace=True)
    dup_removed = before_dedup - len(df)
    logs.append(f"LIMPIEZA: Duplicados eliminados: {dup_removed} ({dup_removed/before_dedup*100:.1f}% del total)")

    errores_ortograficos = {
        'diabetis': 'Diabetes Tipo 2',
        'diabetes tipo 2': 'Diabetes Tipo 2',
        'diabetes tipo2': 'Diabetes Tipo 2',
        'hipertensión': 'Hipertensión',
        'hipertension': 'Hipertensión',
    }

    ortograficos_antes = 0
    if 'diagnostico_preliminar' in df.columns:
        df['diagnostico_preliminar'] = df['diagnostico_preliminar'].astype(str)
        for err, corr in errores_ortograficos.items():
            mask = df['diagnostico_preliminar'].str.lower().str.strip() == err.lower().strip()
            ortograficos_antes += mask.sum()
            df.loc[mask, 'diagnostico_preliminar'] = corr
    logs.append(f"LIMPIEZA: Errores ortográficos corregidos: {ortograficos_antes}")

    if 'antecedentes_familiares' in df.columns:
        na_antes = df['antecedentes_familiares'].isna().sum()
        df['antecedentes_familiares'] = df['antecedentes_familiares'].fillna('Ninguno')
        logs.append(f"LIMPIEZA: Antecedentes nulos rellenados: {na_antes}")

    for col in ['fumador', 'consumo_alcohol']:
        if col in df.columns:
            df[col] = df[col].astype(str)
            bool_mask = df[col].isin(['True', 'False'])
            if bool_mask.any():
                logs.append(f"LIMPIEZA: Valores booleanos convertidos a texto en '{col}': {bool_mask.sum()}")
                df.loc[df[col] == 'True', col] = 'Sí'
                df.loc[df[col] == 'False', col] = 'No'
            df[col] = df[col].str.replace('Si', 'Sí', case=False)
            df[col] = df[col].str.replace('si', 'Sí', case=False)
            df[col] = df[col].str.replace('no', 'No', case=False)
    logs.append("LIMPIEZA: Normalización de fumador/consumo_alcohol aplicada")

    if 'sexo' in df.columns:
        df['sexo'] = df['sexo'].astype(str).replace({'M': 'Masculino', 'F': 'Femenino', 'm': 'Masculino', 'f': 'Femenino'})
        logs.append(f"LIMPIEZA: Sexo normalizado")

    for col in ['nombres', 'apellidos']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.title()

    df['edad'] = pd.to_numeric(df['edad'], errors='coerce')
    df['peso'] = pd.to_numeric(df['peso'], errors='coerce')
    df['glucosa'] = pd.to_numeric(df['glucosa'], errors='coerce')
    df['colesterol'] = pd.to_numeric(df['colesterol'], errors='coerce')

    logs.append("CONVERSIÓN: Tipos numéricos convertidos (edad, peso, glucosa, colesterol)")

    outliers_peso = (df['peso'] > 300).sum()
    df.loc[df['peso'] > 300, 'peso'] = df.loc[df['peso'] > 300, 'peso'] / 100
    if outliers_peso:
        logs.append(f"LIMPIEZA: Valores atípicos de peso corregidos (divididos /100): {outliers_peso}")

    null_info = []
    for col in ['edad', 'peso', 'glucosa', 'colesterol', 'presion_sistolica', 'presion_diastolica',
                'frecuencia_cardiaca', 'saturacion_oxigeno', 'temperatura', 'altura']:
        nulos = df[col].isna().sum()
        if nulos > 0:
            null_info.append(f"{col}: {nulos}")

    df['edad'] = df['edad'].fillna(df['edad'].median()).astype(int)
    df['peso'] = df['peso'].fillna(df['peso'].median()).round(1)
    df['glucosa'] = df['glucosa'].fillna(df['glucosa'].median()).round(1)
    df['colesterol'] = df['colesterol'].fillna(df['colesterol'].median()).round(1)
    df['presion_sistolica'] = pd.to_numeric(df['presion_sistolica'], errors='coerce').fillna(df['presion_sistolica'].median()).astype(int)
    df['presion_diastolica'] = pd.to_numeric(df['presion_diastolica'], errors='coerce').fillna(df['presion_diastolica'].median()).astype(int)
    df['frecuencia_cardiaca'] = pd.to_numeric(df['frecuencia_cardiaca'], errors='coerce').fillna(df['frecuencia_cardiaca'].median()).astype(int)
    df['saturacion_oxigeno'] = pd.to_numeric(df['saturacion_oxigeno'], errors='coerce').fillna(df['saturacion_oxigeno'].median()).round(1)
    df['temperatura'] = pd.to_numeric(df['temperatura'], errors='coerce').fillna(df['temperatura'].mean()).round(1)

    if 'altura' in df.columns:
        df['altura'] = pd.to_numeric(df['altura'], errors='coerce')
        df['altura'] = df['altura'].fillna(df['altura'].median())

    nulls_despues = df.isnull().sum().sum()
    if null_info:
        logs.append(f"NULOS: Valores nulos encontrados y tratados: {', '.join(null_info)}")
    logs.append(f"NULOS: Total nulos inicial: {nulls_original}, después: {nulls_despues}")

    if 'IMC' not in df.columns or df['IMC'].isnull().all():
        df['IMC'] = df['peso'] / (df['altura'] ** 2)
    else:
        df['IMC'] = pd.to_numeric(df['IMC'], errors='coerce')
        imc_nulos = df['IMC'].isnull()
        df.loc[imc_nulos, 'IMC'] = df.loc[imc_nulos, 'peso'] / (df.loc[imc_nulos, 'altura'] ** 2)

    df['IMC'] = df['IMC'].round(1)
    logs.append("CÁLCULO: IMC = peso / altura² (calculado automáticamente)")

    def clasificar_riesgo(row):
        imc = row['IMC'] if pd.notna(row['IMC']) else 0
        glu = row['glucosa'] if pd.notna(row['glucosa']) else 0
        col = row['colesterol'] if pd.notna(row['colesterol']) else 0
        sis = row['presion_sistolica'] if pd.notna(row['presion_sistolica']) else 0
        edad = row['edad'] if pd.notna(row['edad']) else 0
        if imc >= 30 and (glu > 140 or col > 240):
            return 'Crítico'
        elif glu > 140 or col > 240 or sis > 160:
            return 'Alto'
        elif edad > 65 or imc > 27:
            return 'Medio'
        return 'Bajo'

    riesgos_antes = df['riesgo_enfermedad'].value_counts().to_dict()
    df['riesgo_enfermedad'] = df.apply(clasificar_riesgo, axis=1)
    riesgos_despues = df['riesgo_enfermedad'].value_counts().to_dict()
    logs.append(f"CLASIFICACIÓN: Riesgo recalculado - {dict(riesgos_despues)}")
    logs.append(f"RESUMEN: {len(df)} registros después de transformación")

    return df, logs


@transaction.atomic
def load(df, user=None):
    logs = []
    cargados = 0
    actualizados = 0
    archivo_nombre = "dataset_clinico"

    for _, row in df.iterrows():
        try:
            def safe(val, default=''):
                return str(val) if pd.notna(val) else default

            fecha = row.get('fecha_consulta')
            if isinstance(fecha, str):
                try:
                    fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
                except:
                    fecha = datetime.now().date()
            elif pd.isna(fecha):
                fecha = datetime.now().date()

            paciente_data = {
                'id_paciente': safe(row.get('id_paciente', '')),
                'nombres': safe(row.get('nombres', '')).title(),
                'apellidos': safe(row.get('apellidos', '')).title(),
                'edad': int(row['edad']) if pd.notna(row.get('edad')) else 0,
                'sexo': safe(row.get('sexo', ''), ''),
                'peso': float(row['peso']) if pd.notna(row.get('peso')) else 0,
                'altura': float(row['altura']) if pd.notna(row.get('altura')) else 1.65,
                'IMC': float(row['IMC']) if pd.notna(row.get('IMC')) else 0,
                'presion_sistolica': int(row['presion_sistolica']) if pd.notna(row.get('presion_sistolica')) else 120,
                'presion_diastolica': int(row['presion_diastolica']) if pd.notna(row.get('presion_diastolica')) else 80,
                'frecuencia_cardiaca': int(row['frecuencia_cardiaca']) if pd.notna(row.get('frecuencia_cardiaca')) else 75,
                'glucosa': float(row['glucosa']) if pd.notna(row.get('glucosa')) else 0,
                'colesterol': float(row['colesterol']) if pd.notna(row.get('colesterol')) else 0,
                'saturacion_oxigeno': float(row['saturacion_oxigeno']) if pd.notna(row.get('saturacion_oxigeno')) else 96,
                'temperatura': float(row['temperatura']) if pd.notna(row.get('temperatura')) else 36.5,
                'antecedentes_familiares': safe(row.get('antecedentes_familiares', 'Ninguno'), 'Ninguno'),
                'fumador': safe(row.get('fumador', 'No'), 'No'),
                'consumo_alcohol': safe(row.get('consumo_alcohol', 'No'), 'No'),
                'actividad_fisica': safe(row.get('actividad_fisica', 'Sedentario'), 'Sedentario'),
                'diagnostico_preliminar': safe(row.get('diagnostico_preliminar', ''), ''),
                'riesgo_enfermedad': safe(row.get('riesgo_enfermedad', 'Bajo'), 'Bajo'),
                'fecha_consulta': fecha,
            }

            obj, created = Paciente.objects.update_or_create(
                id_paciente=paciente_data['id_paciente'],
                defaults=paciente_data
            )
            if created:
                cargados += 1
            else:
                actualizados += 1
        except Exception as e:
            logs.append(f"LOAD: Error con {row.get('id_paciente', 'DESCONOCIDO')}: {str(e)}")
            continue

    total = cargados + actualizados
    logs.append(f"CARGA: Nuevos: {cargados}, Actualizados: {actualizados}, Total: {total}")
    logs.append(f"CARGA: Datos guardados correctamente en la base de datos")

    return {'cargados': cargados, 'actualizados': actualizados, 'total': total, 'logs': logs, 'archivo': archivo_nombre}


def run_etl(file_path, user=None):
    start_time = time.time()
    all_logs = []

    try:
        df, logs_extract = extract(file_path)
        all_logs.extend(logs_extract)
        registros_iniciales = len(df)

        all_logs.append("--- INICIO TRANSFORMACIÓN ---")
        df, logs_transform = transform(df)
        all_logs.extend(logs_transform)
        all_logs.append("--- FIN TRANSFORMACIÓN ---")
        registros_finales = len(df)

        all_logs.append("--- INICIO CARGA ---")
        result = load(df, user)
        all_logs.extend(result['logs'])
        all_logs.append("--- FIN CARGA ---")

        elapsed = round(time.time() - start_time, 2)

        historial = HistorialETL.objects.create(
            usuario=user,
            archivo=result.get('archivo', file_path),
            registros_procesados=registros_iniciales,
            registros_limpios=registros_finales,
            tiempo_ejecucion=elapsed,
            estado='Completado',
            logs='\n'.join(all_logs)
        )

        return {
            'success': True,
            'historial_id': historial.id,
            'registros_iniciales': registros_iniciales,
            'registros_finales': registros_finales,
            'tiempo_ejecucion': elapsed,
            'logs': all_logs
        }

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        all_logs.append(f"ERROR: {str(e)}")
        import traceback
        all_logs.append(traceback.format_exc())

        HistorialETL.objects.create(
            usuario=user,
            archivo=file_path,
            registros_procesados=0,
            registros_limpios=0,
            tiempo_ejecucion=elapsed,
            estado='Error',
            logs='\n'.join(all_logs)
        )

        return {'success': False, 'error': str(e), 'tiempo_ejecucion': elapsed, 'logs': all_logs}
