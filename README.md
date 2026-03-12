# Simple TLS — Training & Learning System

Sistema de gestión de aprendizaje (LMS) diseñado para capacitación empresarial. Permite a los administradores crear cursos con contenido multimedia, evaluar a los empleados con exámenes automatizados, y hacer seguimiento del progreso de cumplimiento por departamento.

## ✨ Características

### Para Administradores
- **Gestión de Cursos:** Crear cursos con módulos y lecciones (HTML, Video, Audio, PDF)
- **Constructor de Evaluaciones:** Crear exámenes con preguntas de opción múltiple, puntaje personalizable, límite de tiempo e intentos
- **Inscripciones Masivas:** Asignar cursos a empleados individuales o departamentos completos
- **Calendario de Capacitaciones:** Vista de calendario interactiva (FullCalendar.js) con fechas límite de completación
- **Gestión de Usuarios:** CRUD de usuarios con roles (admin/empleado) y asignación a departamentos
- **Branding Personalizable:** Logo, favicon, nombre de app y dominio configurables con subida directa de imágenes

### Para Empleados
- **Dashboard Personal:** Vista de cursos inscritos con barra de progreso
- **Visor de Contenido:** Reproductor integrado para HTML, video, audio y PDF
- **Progreso Automático:** Tracking automático de lecciones completadas (video/audio) y manual (otros tipos)
- **Exámenes en Línea:** Interfaz de examen con timer visual y calificación automática
- **Navegación Secuencial:** Desbloqueo progresivo de lecciones según avance

### API REST para IA
- **Generación Automática de Cursos:** Endpoint para crear un curso completo (módulos, lecciones, evaluaciones, preguntas) en una sola llamada JSON
- Ideal para integrar con agentes de IA que generen programas de capacitación a partir de un tema

## 🏗️ Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.12, Flask |
| Base de Datos | PostgreSQL 16 |
| ORM | SQLAlchemy + Alembic (migraciones) |
| Almacenamiento | MinIO (S3-compatible) |
| Frontend | Jinja2 + TailwindCSS (CDN) + Font Awesome |
| Autenticación | Flask-Login + Bcrypt |
| Contenedores | Docker + Docker Compose |

## 🚀 Instalación

### Prerrequisitos
- Docker y Docker Compose instalados

### Levantar el sistema

```bash
# Clonar el repositorio
git clone https://github.com/jpalmae/simple-tls.git
cd simple-tls

# Levantar los 3 contenedores (web, postgres, minio)
docker compose up -d --build

# Ejecutar migraciones de base de datos
docker compose exec web flask db upgrade

# Crear usuario administrador
docker compose exec web python create_admin.py
```

La aplicación estará disponible en **http://localhost:8080**

### Credenciales por defecto
- **Email:** `admin@sixmanager.cl`
- **Password:** `SixManager2026!`

## 📁 Estructura del Proyecto

```
lms/
├── app/
│   ├── __init__.py              # Application factory
│   ├── config.py                # Configuración (env vars)
│   ├── models/                  # Modelos SQLAlchemy
│   │   ├── usuario.py           # Usuarios y roles
│   │   ├── departamento.py      # Departamentos
│   │   ├── curso.py             # Cursos, Módulos, Lecciones
│   │   ├── evaluacion.py        # Evaluaciones, Preguntas, Opciones
│   │   ├── inscripcion.py       # Inscripciones, Progreso, Intentos
│   │   ├── configuracion.py     # Config global y branding
│   │   └── certificado.py       # Certificados (futuro)
│   ├── routes/
│   │   ├── auth.py              # Login, Logout, Redirect
│   │   ├── admin/               # Rutas de administración
│   │   │   ├── usuarios.py      # CRUD usuarios
│   │   │   ├── configuracion.py # Branding y config global
│   │   │   ├── inscripciones_bp.py  # Gestión de inscripciones
│   │   │   └── cursos/          # Gestión de cursos
│   │   │       ├── cursos_bp.py
│   │   │       ├── modulos_bp.py
│   │   │       ├── lecciones_bp.py
│   │   │       └── evaluaciones_bp.py
│   │   ├── empleado/            # Rutas de empleados
│   │   │   ├── cursos_bp.py     # Dashboard y detalle
│   │   │   ├── visor_bp.py      # Reproductor de contenido
│   │   │   └── evaluacion_bp.py # Exámenes
│   │   └── api/
│   │       └── v1.py            # API REST para IA
│   ├── services/
│   │   ├── auth_service.py      # User loader
│   │   └── minio_service.py     # Upload/download de archivos
│   ├── templates/               # Templates Jinja2
│   └── utils/
│       └── decorators.py        # @admin_required
├── migrations/                  # Alembic migrations
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🔌 API REST

Autenticación vía header `X-API-Key`.

### Crear curso completo
```bash
POST /api/v1/curso-completo

curl -X POST http://localhost:8080/api/v1/curso-completo \
  -H "Content-Type: application/json" \
  -H "X-API-Key: lms-api-key-2026" \
  -d '{
    "titulo": "Seguridad Informática 101",
    "descripcion": "Curso introductorio...",
    "activo": true,
    "modulos": [
      {
        "titulo": "Módulo 1: Fundamentos",
        "orden": 1,
        "lecciones": [
          {
            "titulo": "Introducción",
            "tipo": "html",
            "contenido": "<h2>Contenido</h2><p>...</p>",
            "duracion_min": 15,
            "orden": 1
          }
        ]
      }
    ],
    "evaluaciones": [
      {
        "titulo": "Examen Final",
        "nota_minima_aprobacion": 70,
        "intentos_maximos": 2,
        "preguntas": [
          {
            "enunciado": "¿Qué es el phishing?",
            "tipo": "multiple",
            "puntaje": 50,
            "opciones": [
              {"texto": "Respuesta correcta", "es_correcta": true},
              {"texto": "Distractor", "es_correcta": false}
            ]
          }
        ]
      }
    ]
  }'
```

### Listar cursos
```bash
GET /api/v1/cursos
```

### Detalle de un curso
```bash
GET /api/v1/curso/<id>
```

## ⚙️ Variables de Entorno

| Variable | Descripción | Default |
|---|---|---|
| `DATABASE_URL` | Connection string PostgreSQL | — |
| `MINIO_ENDPOINT` | Hostname interno de MinIO | `minio:9000` |
| `MINIO_PUBLIC_ENDPOINT` | Hostname accesible desde el navegador | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minio_admin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minio_password` |
| `MINIO_BUCKET` | Nombre del bucket | `lms-assets` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |

## 📝 Licencia

MIT
