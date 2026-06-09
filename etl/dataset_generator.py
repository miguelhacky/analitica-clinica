import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

def generar_dataset(path, registros=1800):
    np.random.seed(42)
    random.seed(42)

    nombres = ['Carlos', 'María', 'Juan', 'Ana', 'Pedro', 'Luisa', 'José', 'Elena', 'Miguel', 'Sofía',
               'Andrés', 'Laura', 'Diego', 'Valentina', 'Felipe', 'Carolina', 'Sergio', 'Isabel', 'Ricardo', 'Patricia']
    apellidos = ['García', 'Rodríguez', 'Martínez', 'López', 'Hernández', 'González', 'Pérez', 'Álvarez',
                 'Ramírez', 'Castro', 'Morales', 'Ortiz', 'Silva', 'Torres', 'Vargas', 'Rojas', 'Cruz', 'Mendoza']
    sexos = ['Masculino', 'Femenino']
    dx_posibles = ['Hipertensión', 'Diabetes Tipo 2', 'Obesidad', 'Asma', 'Artritis',
                   'Enfermedad Cardiovascular', 'Ninguno', 'Diabetes Tipo 1', 'Hipotiroidismo', 'Anemia']
    riesgos = ['Bajo', 'Medio', 'Alto', 'Crítico']
    actividades = ['Sedentario', 'Moderado', 'Activo', 'Intenso']
    si_no = ['Sí', 'No']
    antecedentes = ['Diabetes', 'Hipertensión', 'Cáncer', 'Cardiopatía', 'Ninguno']

    data = []
    for i in range(1, registros + 1):
        is_error = np.random.random() < 0.08

        id_pac = f"PAC-{i:04d}"
        nom = random.choice(nombres)
        ape = random.choice(apellidos)
        edad = int(np.random.normal(45, 15))

        if is_error and np.random.random() < 0.15:
            nom = nom.lower()

        if edad < 10: edad = 10
        if edad > 90: edad = 90

        sex = random.choice(sexos)

        peso = float(np.random.normal(72, 12))
        altura = float(np.random.normal(1.65, 0.10))

        if is_error and np.random.random() < 0.15:
            peso = peso * 100

        if altura < 1.20: altura = 1.20
        if altura > 2.00: altura = 2.00
        if peso < 35: peso = 35
        if peso > 150: peso = 150

        imc = round(peso / (altura ** 2), 1)

        presion_sis = int(np.random.normal(125, 15))
        presion_dis = int(np.random.normal(80, 10))

        if edad > 60 and np.random.random() < 0.3:
            presion_sis += 15

        if presion_sis < 90: presion_sis = 90
        if presion_sis > 200: presion_sis = 200
        if presion_dis < 50: presion_dis = 50
        if presion_dis > 120: presion_dis = 120

        fc = int(np.random.normal(75, 12))
        if fc < 40: fc = 40
        if fc > 120: fc = 120

        glucosa = float(np.random.normal(100, 25))
        if glucosa < 50: glucosa = 50
        if glucosa > 350: glucosa = 350

        colesterol = float(np.random.normal(195, 40))
        if colesterol < 100: colesterol = 100
        if colesterol > 350: colesterol = 350

        spo2 = float(np.random.normal(96, 2))
        if spo2 < 80: spo2 = 80
        if spo2 > 100: spo2 = 100

        temp = float(np.random.normal(36.5, 0.4))
        if temp < 35: temp = 35
        if temp > 40: temp = 40

        ant = random.choice(antecedentes)
        fum = random.choice(si_no)
        alcohol = random.choice(si_no)
        act = random.choice(actividades)

        if edad > 60:
            dx_probs = [0.25, 0.20, 0.15, 0.05, 0.10, 0.15, 0.05, 0.02, 0.02, 0.01]
        elif edad > 35:
            dx_probs = [0.15, 0.15, 0.15, 0.05, 0.08, 0.08, 0.18, 0.03, 0.03, 0.10]
        else:
            dx_probs = [0.05, 0.03, 0.08, 0.10, 0.02, 0.02, 0.50, 0.05, 0.05, 0.10]

        dx_probs = np.array(dx_probs)
        dx_probs = dx_probs / dx_probs.sum()
        dx = np.random.choice(dx_posibles, p=dx_probs)

        if imc >= 30:
            riesgo = 'Crítico' if (glucosa > 140 and colesterol > 240) else ('Alto' if (glucosa > 125 or colesterol > 220) else 'Medio')
        elif glucosa > 140 or colesterol > 240 or presion_sis > 160:
            riesgo = 'Alto' if (glucosa > 160 or colesterol > 260) else 'Medio'
        elif edad > 65 or fum == 'Sí' or imc > 27:
            riesgo = 'Medio'
        else:
            riesgo = 'Bajo'

        if is_error and np.random.random() < 0.12:
            riesgo = 'Desconocido'

        fecha_consulta = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 500))
        fecha_consulta = fecha_consulta.strftime('%Y-%m-%d')

        row = {
            'id_paciente': id_pac,
            'nombres': nom,
            'apellidos': ape,
            'edad': edad,
            'sexo': sex,
            'peso': peso,
            'altura': altura,
            'IMC': imc,
            'presión_sistólica': presion_sis,
            'presión_diastólica': presion_dis,
            'frecuencia_cardiaca': fc,
            'glucosa': glucosa,
            'colesterol': colesterol,
            'saturación_oxígeno': spo2,
            'temperatura': temp,
            'antecedentes_familiares': ant,
            'fumador': fum,
            'consumo_alcohol': alcohol,
            'actividad_física': act,
            'diagnóstico_preliminar': dx,
            'riesgo_enfermedad': riesgo,
            'fecha_consulta': fecha_consulta,
        }

        if is_error:
            err_type = np.random.random()
            if err_type < 0.20:
                row['edad'] = f"{edad}años"
            elif err_type < 0.35:
                row['fumador'] = 'Si'
            elif err_type < 0.50:
                row['sexo'] = 'M' if sex == 'Masculino' else 'F'
            elif err_type < 0.60:
                row['glucosa'] = None
            elif err_type < 0.70:
                row['colesterol'] = None
            elif err_type < 0.80:
                row['IMC'] = None
            elif err_type < 0.87:
                row['antecedentes_familiares'] = None
            else:
                row['diagnóstico_preliminar'] = 'diabetis' if dx == 'Diabetes Tipo 2' else 'hipertensión'

        data.append(row)

    df = pd.DataFrame(data)

    duplicate_indices = np.random.choice(range(registros), size=5, replace=False)
    dup_rows = df.iloc[duplicate_indices].copy()
    df = pd.concat([df, dup_rows], ignore_index=True)

    ext = os.path.splitext(path)[1].lower()
    if ext == '.csv':
        df.to_csv(path, index=False, encoding='utf-8')
    elif ext in ['.xlsx', '.xls']:
        df.to_excel(path, index=False, engine='openpyxl')

    print(f"Dataset generado: {len(df)} registros en {path}")
    return path
