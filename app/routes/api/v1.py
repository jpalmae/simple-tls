"""
API REST para generación programática de cursos completos.

Diseñada para ser consumida por un agente de IA que, dado un tema,
genera un payload JSON con curso, módulos, lecciones, evaluaciones,
preguntas y opciones, y los crea en una sola llamada.

Endpoints:
  POST /api/v1/curso-completo   — Crea un curso completo con toda su malla y evaluación.
  GET  /api/v1/cursos            — Lista cursos existentes (resumen).
  GET  /api/v1/curso/<id>        — Detalle completo de un curso con su malla.

Autenticación: API Key via header X-API-Key (simple para MVP).
"""
from functools import wraps
from flask import Blueprint, request, jsonify
from app.models.curso import Curso, Modulo, Leccion
from app.models.evaluacion import Evaluacion, Pregunta, Opcion
from app.models.usuario import Usuario
from app import db

api_v1_bp = Blueprint('api_v1', __name__)

# ─── Autenticación simple por API Key ───────────────────────────
API_KEY_HEADER = 'X-API-Key'

def require_api_key(f):
    """Decorator que valida un API key estático o vinculado a un admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get(API_KEY_HEADER)
        if not api_key:
            return jsonify({'error': 'Falta header X-API-Key'}), 401

        from app.models.configuracion import Configuracion
        config = Configuracion.query.first()
        expected_key = config.api_key if config and hasattr(config, 'api_key') and config.api_key else None

        # Fallback: aceptar la key hardcoded para MVP si no hay configurada
        if not expected_key:
            expected_key = 'lms-api-key-2026'

        if api_key != expected_key:
            return jsonify({'error': 'API Key inválida'}), 403

        return f(*args, **kwargs)
    return decorated


# ─── POST /api/v1/curso-completo ────────────────────────────────
@api_v1_bp.route('/curso-completo', methods=['POST'])
@require_api_key
def crear_curso_completo():
    """
    Crea un curso completo con módulos, lecciones y evaluaciones en una sola llamada.

    Payload JSON esperado:
    {
      "titulo": "Seguridad Informática 101",
      "descripcion": "Curso introductorio sobre seguridad...",
      "secuencial": true,
      "activo": true,
      "modulos": [
        {
          "titulo": "Módulo 1: Fundamentos",
          "orden": 1,
          "lecciones": [
            {
              "titulo": "¿Qué es la seguridad informática?",
              "tipo": "html",
              "contenido": "<h2>Introducción</h2><p>La seguridad informática es...</p>",
              "duracion_min": 10,
              "orden": 1
            }
          ]
        }
      ],
      "evaluaciones": [
        {
          "titulo": "Examen Final",
          "instrucciones": "Seleccione la respuesta correcta...",
          "nota_minima_aprobacion": 70,
          "intentos_maximos": 3,
          "tiempo_limite_min": 30,
          "preguntas": [
            {
              "enunciado": "¿Cuál es el principio CIA?",
              "tipo": "multiple",
              "puntaje": 10,
              "orden": 1,
              "opciones": [
                {"texto": "Confidencialidad, Integridad, Disponibilidad", "es_correcta": true},
                {"texto": "Control, Implementación, Auditoría", "es_correcta": false}
              ]
            }
          ]
        }
      ]
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Se requiere un payload JSON'}), 400

    if not data.get('titulo'):
        return jsonify({'error': 'El campo "titulo" es obligatorio'}), 400

    # Obtener un admin por defecto como creador
    admin = Usuario.query.filter_by(rol='admin').first()
    if not admin:
        return jsonify({'error': 'No existe un usuario admin en el sistema'}), 500

    try:
        # 1. Crear el curso
        curso = Curso(
            titulo=data['titulo'],
            descripcion=data.get('descripcion', ''),
            secuencial=data.get('secuencial', True),
            activo=data.get('activo', True),
            creado_por=admin.id
        )
        db.session.add(curso)
        db.session.flush()  # Para obtener curso.id

        leccion_global_orden = 1
        resumen_modulos = []

        # 2. Crear módulos y lecciones
        for mod_data in data.get('modulos', []):
            modulo = Modulo(
                curso_id=curso.id,
                titulo=mod_data['titulo'],
                orden=mod_data.get('orden', 1)
            )
            db.session.add(modulo)
            db.session.flush()

            lecciones_creadas = []
            for lec_data in mod_data.get('lecciones', []):
                leccion = Leccion(
                    curso_id=curso.id,
                    modulo_id=modulo.id,
                    titulo=lec_data['titulo'],
                    tipo=lec_data.get('tipo', 'html'),
                    contenido=lec_data.get('contenido', ''),
                    duracion_min=lec_data.get('duracion_min'),
                    orden=lec_data.get('orden', leccion_global_orden)
                )
                db.session.add(leccion)
                leccion_global_orden += 1
                lecciones_creadas.append(lec_data['titulo'])

            resumen_modulos.append({
                'modulo': mod_data['titulo'],
                'lecciones': len(lecciones_creadas)
            })

        # 3. Crear evaluaciones
        resumen_evals = []
        for eval_data in data.get('evaluaciones', []):
            evaluacion = Evaluacion(
                curso_id=curso.id,
                titulo=eval_data['titulo'],
                instrucciones=eval_data.get('instrucciones', ''),
                nota_minima_aprobacion=eval_data.get('nota_minima_aprobacion', 60),
                intentos_maximos=eval_data.get('intentos_maximos', 3),
                tiempo_limite_min=eval_data.get('tiempo_limite_min'),
                aleatorizar_preguntas=eval_data.get('aleatorizar_preguntas', False),
                aleatorizar_opciones=eval_data.get('aleatorizar_opciones', False)
            )
            db.session.add(evaluacion)
            db.session.flush()

            preguntas_count = 0
            for preg_data in eval_data.get('preguntas', []):
                pregunta = Pregunta(
                    evaluacion_id=evaluacion.id,
                    enunciado=preg_data['enunciado'],
                    tipo=preg_data.get('tipo', 'multiple'),
                    puntaje=preg_data.get('puntaje', 1),
                    orden=preg_data.get('orden', preguntas_count + 1)
                )
                db.session.add(pregunta)
                db.session.flush()

                for opc_data in preg_data.get('opciones', []):
                    opcion = Opcion(
                        pregunta_id=pregunta.id,
                        texto=opc_data['texto'],
                        es_correcta=opc_data.get('es_correcta', False)
                    )
                    db.session.add(opcion)

                preguntas_count += 1

            resumen_evals.append({
                'evaluacion': eval_data['titulo'],
                'preguntas': preguntas_count
            })

        db.session.commit()

        return jsonify({
            'success': True,
            'curso_id': curso.id,
            'titulo': curso.titulo,
            'url_admin': f'/admin/cursos/{curso.id}/builder',
            'resumen': {
                'modulos': resumen_modulos,
                'evaluaciones': resumen_evals
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear curso: {str(e)}'}), 500


# ─── GET /api/v1/cursos ─────────────────────────────────────────
@api_v1_bp.route('/cursos', methods=['GET'])
@require_api_key
def listar_cursos():
    """Lista todos los cursos con resumen básico."""
    cursos = Curso.query.order_by(Curso.id.desc()).all()
    resultado = []
    for c in cursos:
        resultado.append({
            'id': c.id,
            'titulo': c.titulo,
            'descripcion': c.descripcion,
            'activo': c.activo,
            'secuencial': c.secuencial,
            'total_modulos': c.modulos.count(),
            'total_lecciones': c.lecciones.count(),
            'total_evaluaciones': c.evaluaciones.count()
        })
    return jsonify(resultado)


# ─── GET /api/v1/curso/<id> ──────────────────────────────────────
@api_v1_bp.route('/curso/<int:curso_id>', methods=['GET'])
@require_api_key
def detalle_curso(curso_id):
    """Retorna el detalle completo de un curso con toda su malla."""
    curso = Curso.query.get_or_404(curso_id)

    modulos_json = []
    for mod in curso.modulos.order_by(Modulo.orden):
        lecciones_json = []
        for lec in mod.lecciones.order_by(Leccion.orden):
            lecciones_json.append({
                'id': lec.id,
                'titulo': lec.titulo,
                'tipo': lec.tipo,
                'duracion_min': lec.duracion_min,
                'orden': lec.orden
            })
        modulos_json.append({
            'id': mod.id,
            'titulo': mod.titulo,
            'orden': mod.orden,
            'lecciones': lecciones_json
        })

    evaluaciones_json = []
    for ev in curso.evaluaciones:
        preguntas_json = []
        for preg in ev.preguntas.order_by(Pregunta.orden):
            opciones_json = []
            for opc in preg.opciones:
                opciones_json.append({
                    'id': opc.id,
                    'texto': opc.texto,
                    'es_correcta': opc.es_correcta
                })
            preguntas_json.append({
                'id': preg.id,
                'enunciado': preg.enunciado,
                'tipo': preg.tipo,
                'puntaje': preg.puntaje,
                'opciones': opciones_json
            })
        evaluaciones_json.append({
            'id': ev.id,
            'titulo': ev.titulo,
            'nota_minima_aprobacion': ev.nota_minima_aprobacion,
            'intentos_maximos': ev.intentos_maximos,
            'preguntas': preguntas_json
        })

    return jsonify({
        'id': curso.id,
        'titulo': curso.titulo,
        'descripcion': curso.descripcion,
        'activo': curso.activo,
        'secuencial': curso.secuencial,
        'modulos': modulos_json,
        'evaluaciones': evaluaciones_json
    })
