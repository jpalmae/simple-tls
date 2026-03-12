from flask import Blueprint, request, flash, redirect, url_for
from flask_login import login_required
from app.utils.decorators import admin_required
from app.models.curso import Modulo, Curso
from app import db

admin_modulos_bp = Blueprint('admin_modulos', __name__)

@admin_modulos_bp.route('/cursos/<int:curso_id>/modulos/nuevo', methods=['POST'])
@login_required
@admin_required
def crear(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    titulo = request.form.get('titulo')
    
    if not titulo:
        flash('El título del módulo es requerido.', 'danger')
        return redirect(url_for('admin_cursos.builder', id=curso.id))
        
    # Obtener el último orden
    ultimo_modulo = Modulo.query.filter_by(curso_id=curso.id).order_by(Modulo.orden.desc()).first()
    nuevo_orden = (ultimo_modulo.orden + 1) if ultimo_modulo else 1
    
    nuevo_modulo = Modulo(curso_id=curso.id, titulo=titulo, orden=nuevo_orden)
    
    try:
        db.session.add(nuevo_modulo)
        db.session.commit()
        flash(f'Módulo "{titulo}" añadido.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al crear el módulo.', 'danger')
        
    return redirect(url_for('admin_cursos.builder', id=curso.id))

@admin_modulos_bp.route('/modulos/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    modulo = Modulo.query.get_or_404(id)
    curso_id = modulo.curso_id
    
    try:
        db.session.delete(modulo) # Lecciones asocadas se eliminan en cascada
        db.session.commit()
        flash('Módulo eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el módulo.', 'danger')
        
    return redirect(url_for('admin_cursos.builder', id=curso_id))
