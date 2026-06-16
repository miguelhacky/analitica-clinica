# Documentación Técnica — HealthAnalytics IPS

## 1. Descripción General

Plataforma de analítica clínica desarrollada con Django 6.0.6, desplegada en Vercel con base de datos PostgreSQL (Neon) e integración de correos transaccionales mediante Brevo (Sendinblue).

## 2. Arquitectura

```
Frontend (HTML + Bootstrap 5 + JavaScript)
        ↕ API REST (Django REST Framework + JWT)
        ↕
    Django 6.0.6 (WSGI: Vercel Python Runtime)
        ↕
┌─────────────────┬──────────────────┐
│   SQLite (local) │ PostgreSQL (prod) │
│   db.sqlite3     │  Neon Serverless   │
└─────────────────┴──────────────────┘
```

## 3. Credenciales y Variables de Entorno

### 3.1 Entorno Local (`.env`)

```
BREVO_API_KEY=tu_api_key_aqui
BREVO_SMTP_USER=miguelfajardozapata@gmail.com
```

### 3.2 Entorno Producción (Vercel Environment Variables)

| Variable              | Uso                          |
|-----------------------|------------------------------|
| `BREVO_API_KEY`       | API key de Brevo (correos)   |
| `BREVO_SMTP_USER`     | Remitente de correos         |
| `DATABASE_URL`        | Cadena de conexión PostgreSQL|
| `SECRET_KEY`          | Clave secreta de Django      |
| `DEBUG`               | False en producción          |

### 3.3 Usuarios del Sistema

| Correo | Rol | Contraseña |
|---|---|---|
| admin@gmail.com | Administrador | admin1234 |
| prueba1@gmail.com | Médico | (definida por el usuario) |
| prueba2@gmail.com | Analista | (definida por el usuario) |

## 4. Configuración de Servicios Externos

### 4.1 Brevo (Correos Transaccionales)

- API key configurada en Vercel env vars y `.env` local
- Remitente verificado: miguelfajardozapata@gmail.com
- IP autorizadas: desactivada la restricción de IPs para API keys
- SDK: `sib-api-v3-sdk` (REST API, no SMTP)
- Disparo: solo restablecimiento de contraseña (código de 6 dígitos)

### 4.2 Neon (PostgreSQL Serverless)

Host: ep-square-fire-aimwpn29-pooler.c-4.us-east-1.aws.neon.tech
Base de datos: neondb
Integración directa con Vercel (variables de entorno automáticas).

## 5. Base de Datos

### 5.1 Tablas Principales

| Tabla                    | Descripción                    | Registros |
|--------------------------|--------------------------------|-----------|
| `accounts_user`          | Usuarios del sistema           | 3         |
| `core_paciente`          | Pacientes registrados          | 1.801     |
| `core_prediccion`        | Predicciones de riesgo         | 565       |
| `core_contagiousdisease` | Enfermedades contagiosas       | 6         |

### 5.2 Estructura de `core_paciente`

- id (PK), id_paciente (PAC-NNNN), nombres, apellidos
- edad, sexo, peso, altura, IMC
- presion_sistolica, presion_diastolica, frecuencia_cardiaca
- glucosa, colesterol, saturacion_oxigeno, temperatura
- antecedentes_familiares, fumador, consumo_alcohol, actividad_fisica
- diagnostico_preliminar, riesgo_enfermedad
- fecha_consulta, estado (Activo/Hospitalizado/Dado de Alta/Fallecido)
- fecha_alta, fecha_fallecimiento, necesidades_cuidado
- piso, ubicacion (Consulta Externa/UCI/Urgencias)

## 6. Endpoints de la API

| Endpoint                              | Método | Auth     | Descripción               |
|---------------------------------------|--------|----------|---------------------------|
| `/api/auth/login/`                    | POST   | No       | Login JWT                 |
| `/api/auth/session-login/`            | POST   | No       | Login por sesión          |
| `/api/auth/register/`                 | POST   | No       | Registro de usuarios      |
| `/api/auth/profile/`                  | GET/POST | Sesión  | Perfil + foto             |
| `/api/auth/password-reset/send-code/` | POST   | No       | Enviar código al correo   |
| `/api/auth/password-reset/verify-code/` | POST | No       | Verificar código          |
| `/api/auth/password-reset/change/`    | POST   | No       | Cambiar contraseña        |
| `/api/dashboard/kpis/`               | GET    | JWT      | KPIs del dashboard        |
| `/api/setup/`                        | GET    | No       | Migrar + cargar fixture   |
| `/api/test-email/`                   | POST   | No       | Probar envío de correo    |
| `/api/media/<path>`                  | GET    | Sesión   | Servir archivos media     |

## 7. Despliegue

### 7.1 Vercel

- URL: https://analitica-clinica-main.vercel.app
- Runtime: Python 3.12 (uv package manager)
- Build: `api/index.py` (WSGI handler)
- Static files: WhiteNoise + CompressedStaticFilesStorage
- Media files: `/tmp/analitica-media` (efímero, se pierde en cold starts)

### 7.2 Git (GitHub)

- Repositorio: miguelhacky/analitica-clinica
- Rama principal: master
- `.env` excluido vía `.gitignore`

## 8. Correcciones Realizadas

1. **Despliegue en Vercel** — Configuración de serverless Python + Neon PostgreSQL
2. **Imágenes estáticas** — Corrección de nombres (Inicio.jpeg con mayúscula), WhiteNoise configurado
3. **Carga de datos** — 1.801 pacientes exportados a fixture UTF-8 y cargados en PostgreSQL
4. **Correos electrónicos** — Desactivación de restricción de IPs en Brevo para API keys
5. **Foto de perfil** — Almacenamiento en `/tmp/` en producción + vista personalizada para servir archivos
6. **Auto-upload** — La foto de perfil se sube automáticamente al seleccionar el archivo
7. **Error handling** — Mejora en la respuesta de errores del envío de correos

## 9. Ejecución Local

```bash
cd analitica-clinica-main
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py runserver 8000
```

Luego abrir http://127.0.0.1:8000/

---
*Documentación generada el 16 de junio de 2026*
