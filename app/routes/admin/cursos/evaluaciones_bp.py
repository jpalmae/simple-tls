from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.curso import Curso
from app.models.evaluacion import Evaluacion, Pregunta, Opcion
from app.utils.decorators import admin_required
from app import db

admin_evaluaciones_bp = Blueprint('admin_evaluaciones', __name__)

@admin_evaluaciones_bp.route('/cursos/<int:curso_id>/evaluaciones')
@login_required
@admin_required
def index(curso_id):
    """Lista las evaluaciones de un curso específico."""
    curso = Curso.query.get_or_404(curso_id)
    evaluaciones = curso.evaluaciones.order_by(Evaluacion.id.desc()).all()
    return render_template('admin/cursos/evaluaciones/list.html', curso=curso, evaluaciones=evaluaciones)

@admin_evaluaciones_bp.route('/cursos/<int:curso_id>/evaluaciones/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear(curso_id):
    """Crea una nueva evaluación para el curso."""
    curso = Curso.query.get_or_404(curso_id)
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        instrucciones = request.form.get('instrucciones')
        nota_minima = int(request.form.get('nota_minima_aprobacion', 60))
        intentos = int(request.form.get('intentos_maximos', 3))
        tiempo = request.form.get('tiempo_limite_min')
        
        tiempo_val = int(tiempo) if tiempo and tiempo.strip() else None
        
        nueva_eval = Evaluacion(
            curso_id=curso.id,
            titulo=titulo,
            instrucciones=instrucciones,
            nota_minima_aprobacion=nota_minima,
            intentos_maximos=intentos,
            tiempo_limite_min=tiempo_val,
            aleatorizar_preguntas=True if request.form.get('aleatorizar_preguntas') else False,
            aleatorizar_opciones=True if request.form.get('aleatorizar_opciones') else False
        )
        
        db.session.add(nueva_eval)
        db.session.commit()
        flash('Evaluación creada correctamente.', 'success')
        return redirect(url_for('admin_evaluaciones.builder', curso_id=curso.id, eval_id=nueva_eval.id))
        
    return render_template('admin/cursos/evaluaciones/form.html', curso=curso, evaluacion=None)

@admin_evaluaciones_bp.route('/cursos/<int:curso_id>/evaluaciones/<int:eval_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(curso_id, eval_id):
    """Edita la configuración de una evaluación."""
    curso = Curso.query.get_or_404(curso_id)
    evaluacion = Evaluacion.query.get_or_404(eval_id)
    
    if request.method == 'POST':
        evaluacion.titulo = request.form.get('titulo')
        evaluacion.instrucciones = request.form.get('instrucciones')
        evaluacion.nota_minima_aprobacion = int(request.form.get('nota_minima_aprobacion', 60))
        evaluacion.intentos_maximos = int(request.form.get('intentos_maximos', 3))
        tiempo = request.form.get('tiempo_limite_min')
        evaluacion.tiempo_limite_min = int(tiempo) if tiempo and tiempo.strip() else None
        evaluacion.aleatorizar_preguntas = True if request.form.get('aleatorizar_preguntas') else False
        evaluacion.aleatorizar_opciones = True if request.form.get('aleatorizar_opciones') else False
        
        db.session.commit()
        flash('Evaluación actualizada correctamente.', 'success')
        return redirect(url_for('admin_evaluaciones.index', curso_id=curso.id))
        
    return render_template('admin/cursos/evaluaciones/form.html', curso=curso, evaluacion=evaluacion)

@admin_evaluaciones_bp.route('/cursos/<int:curso_id>/evaluaciones/<int:eval_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar(curso_id, eval_id):
    """Elimina una evaluación."""
    evaluacion = Evaluacion.query.get_or_404(eval_id)
    db.session.delete(evaluacion)
    db.session.commit()
    flash('Evaluación eliminada correctamente.', 'success')
    return redirect(url_for('admin_evaluaciones.index', curso_id=curso_id))

@admin_evaluaciones_bp.route('/cursos/<int:curso_id>/evaluaciones/<int:eval_id>/builder')
@login_required
@admin_required
def builder(curso_id, eval_id):
    """Constructor visual para agregar preguntas y opciones."""
    curso = Curso.query.get_or_404(curso_id)
    evaluacion = Evaluacion.query.get_or_404(eval_id)
    return render_template('admin/cursos/evaluaciones/builder.html', curso=curso, evaluacion=evaluacion)

@admin_evaluaciones_bp.route('/cursos/<int:curso_id>/evaluaciones/<int:eval_id>/pregunta', methods=['POST'])
@login_required
@admin_required
def agregar_pregunta(curso_id, eval_id):
    """API: Agrega una pregunta a la evaluación."""
    evaluacion = Evaluacion.query.get_or_404(eval_id)
    
    enunciado = request.form.get('enunciado')
    tipo = request.form.get('tipo', 'multiple')
    puntaje = int(request.form.get('puntaje', 1))
    
    # Calcular orden
    ultima = evaluacion.preguntas.order_by(Pregunta.orden.desc()).first()
    orden = (ultima.orden + 1) if ultima else 1
    
    pregunta = Pregunta(
        evaluacion_id=evaluacion.id,
        enunciado=enunciado,
        tipo=tipo,
        puntaje=puntaje,
        orden=orden
    )
    db.session.add(pregunta)
    db.session.commit()
    
    flash('Pregunta agregada.', 'success')
    return redirect(url_for('admin_evaluaciones.builder', curso_id=curso_id, eval_id=eval_id))

@admin_evaluaciones_bp.route('/cursos/<int:curso_id>/evaluaciones/<int:eval_id>/pregunta/<int:pregunta_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_pregunta(curso_id, eval_id, pregunta_id):
    """API: Elimina una pregunta."""
    pregunta = Pregunta.query.get_or_404(pregunta_id)
    db.session.delete(pregunta)
    db.session.commit()
    flash('Pregunta eliminada.', 'success')
    return redirect(url_for('admin_evaluaciones.builder', curso_id=curso_id, eval_id=eval_id))

@admin_evaluaciones_bp.route('/cursos/<int:curso_id>/evaluaciones/<int:eval_id>/pregunta/<int:pregunta_id>/opcion', methods=['POST'])
@login_required
@admin_required
def agregar_opcion(curso_id, eval_id, pregunta_id):
    """API: Agrega una opción a una pregunta de selección múltiple."""
    pregunta = Pregunta.query.get_or_404(pregunta_id)
    
    texto = request.form.get('texto')
    es_correcta = True if request.form.get('es_correcta') else False
    
    opcion = Opcion(
        pregunta_id=pregunta.id,
        texto=texto,
        es_correcta=es_correcta
    )
    db.session.add(opcion)
    db.session.commit()
    
    flash('Opción agregada.', 'success')
    return redirect(url_for('admin_evaluaciones.builder', curso_id=curso_id, eval_id=eval_id))

@admin_evaluaciones_bp.route('/cursos/<int:curso_id>/evaluaciones/<int:eval_id>/opcion/<int:opcion_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_opcion(curso_id, eval_id, opcion_id):
    """API: Elimina una opción."""
    opcion = Opcion.query.get_or_404(opcion_id)
    db.session.delete(opcion)
    db.session.commit()
    return redirect(url_for('admin_evaluaciones.builder', curso_id=curso_id, eval_id=eval_id))
