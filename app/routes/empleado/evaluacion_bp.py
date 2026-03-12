from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.models.curso import Curso
from app.models.evaluacion import Evaluacion, Pregunta, Opcion
from app.models.inscripcion import Inscripcion, Intento, RespuestaIntento
from app import db
from datetime import datetime, timezone

empleado_eval_bp = Blueprint('empleado_eval', __name__)

def _validar_acceso_eval(curso_id, eval_id):
    """Helper para verificar inscripción y retornar instancias base."""
    curso = Curso.query.get_or_404(curso_id)
    evaluacion = Evaluacion.query.get_or_404(eval_id)
    
    if evaluacion.curso_id != curso.id:
        abort(404)
        
    inscripcion = Inscripcion.query.filter_by(usuario_id=current_user.id, curso_id=curso.id).first()
    
    if not inscripcion and current_user.rol != 'admin':
        abort(403)
        
    return curso, evaluacion, inscripcion

@empleado_eval_bp.route('/mis-cursos/<int:curso_id>/evaluacion/<int:eval_id>')
@login_required
def intro(curso_id, eval_id):
    """Página de inicio de la evaluación (Reglas, intentos restantes)."""
    curso, evaluacion, inscripcion = _validar_acceso_eval(curso_id, eval_id)
    
    intentos_realizados = 0
    mejor_puntaje = None
    aprobado = False
    
    if inscripcion:
        intentos = Intento.query.filter_by(inscripcion_id=inscripcion.id, evaluacion_id=evaluacion.id).all()
        intentos_realizados = len(intentos)
        
        for intt in intentos:
            if intt.puntaje_obtenido and (mejor_puntaje is None or intt.puntaje_obtenido > mejor_puntaje):
                mejor_puntaje = intt.puntaje_obtenido
            if intt.aprobado:
                aprobado = True

    puede_rendir = True
    if evaluacion.intentos_maximos > 0 and intentos_realizados >= evaluacion.intentos_maximos and not aprobado:
        puede_rendir = False

    return render_template(
        'empleado/evaluacion/intro.html', 
        curso=curso, 
        evaluacion=evaluacion, 
        intentos_realizados=intentos_realizados,
        mejor_puntaje=mejor_puntaje,
        aprobado=aprobado,
        puede_rendir=puede_rendir
    )

@empleado_eval_bp.route('/mis-cursos/<int:curso_id>/evaluacion/<int:eval_id>/iniciar', methods=['POST'])
@login_required
def iniciar(curso_id, eval_id):
    """Crea un nuevo intento y redirige a la prueba."""
    curso, evaluacion, inscripcion = _validar_acceso_eval(curso_id, eval_id)
    
    if not inscripcion:
        flash('Debes estar inscrito para rendir.', 'warning')
        return redirect(url_for('empleado_cursos.detalle', id=curso.id))
        
    # Verificar límites
    intentos_previos = Intento.query.filter_by(inscripcion_id=inscripcion.id, evaluacion_id=evaluacion.id).count()
    if evaluacion.intentos_maximos > 0 and intentos_previos >= evaluacion.intentos_maximos:
        flash('Has superado el límite de intentos.', 'danger')
        return redirect(url_for('empleado_eval.intro', curso_id=curso.id, eval_id=evaluacion.id))
        
    nuevo_intento = Intento(
        inscripcion_id=inscripcion.id,
        evaluacion_id=evaluacion.id,
        fecha_inicio=datetime.now(timezone.utc)
    )
    db.session.add(nuevo_intento)
    db.session.commit()
    
    return redirect(url_for('empleado_eval.rendir', curso_id=curso.id, eval_id=evaluacion.id, intento_id=nuevo_intento.id))

@empleado_eval_bp.route('/mis-cursos/<int:curso_id>/evaluacion/<int:eval_id>/rendir/<int:intento_id>')
@login_required
def rendir(curso_id, eval_id, intento_id):
    """Renderiza el formulario del examen."""
    curso, evaluacion, inscripcion = _validar_acceso_eval(curso_id, eval_id)
    intento = Intento.query.get_or_404(intento_id)
    
    if intento.fecha_fin:
        flash('Este intento ya fue enviado.', 'warning')
        return redirect(url_for('empleado_eval.intro', curso_id=curso.id, eval_id=evaluacion.id))
        
    preguntas = evaluacion.preguntas.order_by('orden').all()
    # TODO: Aleatorizar orden si evaluacion.aleatorizar_preguntas == True
    
    return render_template('empleado/evaluacion/rendir.html', curso=curso, evaluacion=evaluacion, intento=intento, preguntas=preguntas)

@empleado_eval_bp.route('/mis-cursos/<int:curso_id>/evaluacion/<int:eval_id>/rendir/<int:intento_id>/submit', methods=['POST'])
@login_required
def submit(curso_id, eval_id, intento_id):
    """Procesa el examen, calcula el puntaje y redirige al resultado."""
    curso, evaluacion, inscripcion = _validar_acceso_eval(curso_id, eval_id)
    intento = Intento.query.get_or_404(intento_id)
    
    if intento.fecha_fin:
        return redirect(url_for('empleado_eval.resultado', curso_id=curso.id, eval_id=evaluacion.id, intento_id=intento.id))
        
    preguntas = evaluacion.preguntas.all()
    puntaje_total = 0
    puntaje_maximo = 0
    
    for pregunta in preguntas:
        puntaje_maximo += pregunta.puntaje
        respuesta_id_str = request.form.get(f'pregunta_{pregunta.id}')
        
        opcion_seleccionada = None
        if respuesta_id_str:
            opcion_seleccionada = Opcion.query.get(int(respuesta_id_str))
            
        resp_obj = RespuestaIntento(
            intento_id=intento.id,
            pregunta_id=pregunta.id,
            opcion_id=opcion_seleccionada.id if opcion_seleccionada else None
        )
        db.session.add(resp_obj)
        
        if opcion_seleccionada and opcion_seleccionada.es_correcta:
            puntaje_total += pregunta.puntaje
            
    intento.puntaje_obtenido = puntaje_total
    intento.puntaje_maximo = puntaje_maximo
    intento.aprobado = (puntaje_total >= evaluacion.nota_minima_aprobacion)
    intento.fecha_fin = datetime.now(timezone.utc)
    
    # Si aprueba, y asumiendo que es la única evaluación vinculada final del curso, marcamos inscripción terminada (Opcional - Fase 6)
    if intento.aprobado and inscripcion:
         inscripcion.estado = 'aprobado'
         
    db.session.commit()
    
    return redirect(url_for('empleado_eval.resultado', curso_id=curso.id, eval_id=evaluacion.id, intento_id=intento.id))

@empleado_eval_bp.route('/mis-cursos/<int:curso_id>/evaluacion/<int:eval_id>/resultado/<int:intento_id>')
@login_required
def resultado(curso_id, eval_id, intento_id):
    """Muestra el resultado final del intento."""
    curso, evaluacion, inscripcion = _validar_acceso_eval(curso_id, eval_id)
    intento = Intento.query.get_or_404(intento_id)
    
    return render_template('empleado/evaluacion/result.html', curso=curso, evaluacion=evaluacion, intento=intento)
