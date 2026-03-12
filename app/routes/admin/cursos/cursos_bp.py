from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.models.curso import Curso
from app import db, minio_svc
import os

admin_cursos_bp = Blueprint('admin_cursos', __name__)

@admin_cursos_bp.route('/')
@login_required
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    cursos = Curso.query.order_by(Curso.fecha_creacion.desc()).paginate(page=page, per_page=12)
    
    # Enrich courses with signed/absolute URLs for cover images
    for c in cursos.items:
        if c.imagen_portada_url:
            c.cover_url = minio_svc.get_file_url(c.imagen_portada_url)
        else:
            c.cover_url = None
            
    return render_template('admin/cursos/list.html', cursos=cursos)

@admin_cursos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        secuencial = True if request.form.get('secuencial') == 'on' else False
        activo = True if request.form.get('activo') == 'on' else False
        
        nuevo_curso = Curso(
            titulo=titulo,
            descripcion=descripcion,
            secuencial=secuencial,
            activo=activo,
            creado_por=current_user.id
        )
        
        db.session.add(nuevo_curso)
        db.session.flush() # Para obtener ID del curso
        
        # Manejar portada
        portada_file = request.files.get('portada')
        if portada_file and portada_file.filename != '':
            folder = f"cursos/{nuevo_curso.id}"
            object_name = minio_svc.upload_file(
                file_stream=portada_file.stream, 
                original_filename=portada_file.filename, 
                folder_path=folder,
                content_type=portada_file.content_type
            )
            if object_name:
                nuevo_curso.imagen_portada_url = object_name
        
        try:
            db.session.commit()
            flash('Curso creado exitosamente. Ahora puedes agregar el contenido.', 'success')
            return redirect(url_for('admin_cursos.builder', id=nuevo_curso.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el curso: {str(e)}', 'danger')
            
    return render_template('admin/cursos/form.html', curso=None)

@admin_cursos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    curso = Curso.query.get_or_404(id)
    
    # Obtener URL para la imagen actual si existe
    cover_url = minio_svc.get_file_url(curso.imagen_portada_url) if curso.imagen_portada_url else None
    
    if request.method == 'POST':
        curso.titulo = request.form.get('titulo')
        curso.descripcion = request.form.get('descripcion')
        curso.secuencial = True if request.form.get('secuencial') == 'on' else False
        curso.activo = True if request.form.get('activo') == 'on' else False
        
        # Manejar nueva portada
        portada_file = request.files.get('portada')
        if portada_file and portada_file.filename != '':
            # Eliminar la anterior si existía
            if curso.imagen_portada_url:
                minio_svc.delete_file(curso.imagen_portada_url)
                
            folder = f"cursos/{curso.id}"
            object_name = minio_svc.upload_file(
                file_stream=portada_file.stream, 
                original_filename=portada_file.filename, 
                folder_path=folder,
                content_type=portada_file.content_type
            )
            if object_name:
                curso.imagen_portada_url = object_name
                
        try:
            db.session.commit()
            flash('Curso actualizado exitosamente.', 'success')
            return redirect(url_for('admin_cursos.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el curso: {str(e)}', 'danger')
            
    return render_template('admin/cursos/form.html', curso=curso, cover_url=cover_url)

@admin_cursos_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    curso = Curso.query.get_or_404(id)
    
    # 1. Eliminar archivos de lecciones asociados en MinIO
    for leccion in curso.lecciones:
        if leccion.tipo in ['pdf', 'video', 'audio'] and leccion.contenido:
            minio_svc.delete_file(leccion.contenido)
    
    # 2. Eliminar portada en MinIO
    if curso.imagen_portada_url:
        minio_svc.delete_file(curso.imagen_portada_url)
        
    try:
        db.session.delete(curso) # Cascade deletes modules, lessons, evals
        db.session.commit()
        flash('Curso y todo su contenido asociado eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el curso: {str(e)}', 'danger')
        
    return redirect(url_for('admin_cursos.index'))

@admin_cursos_bp.route('/<int:id>/builder')
@login_required
@admin_required
def builder(id):
    """Vista principal para armar el currículum del curso (módulos y lecciones)"""
    curso = Curso.query.get_or_404(id)
    return render_template('admin/cursos/builder.html', curso=curso)
