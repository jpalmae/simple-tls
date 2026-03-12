from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_required
from app.utils.decorators import admin_required
from app.models.curso import Leccion, Curso, Modulo
from app import db, minio_svc
import os

admin_lecciones_bp = Blueprint('admin_lecciones', __name__)

@admin_lecciones_bp.route('/cursos/<int:curso_id>/lecciones/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def crear(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    modulo_id = request.args.get('modulo_id', type=int) # Opcional
    tipo = request.args.get('tipo', 'html')
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        tipo_post = request.form.get('tipo')
        duracion_min = request.form.get('duracion_min', type=int)
        mod_id = request.form.get('modulo_id', type=int) if request.form.get('modulo_id') else None
        
        # Determinar orden
        ultima_leccion = Leccion.query.filter_by(curso_id=curso.id, modulo_id=mod_id).order_by(Leccion.orden.desc()).first()
        nuevo_orden = (ultima_leccion.orden + 1) if ultima_leccion else 1
        
        nueva_leccion = Leccion(
            curso_id=curso.id,
            modulo_id=mod_id,
            titulo=titulo,
            tipo=tipo_post,
            duracion_min=duracion_min,
            orden=nuevo_orden,
            contenido="" # placeholder
        )
        
        # Manejar contenido según tipo
        if tipo_post == 'html':
            import bleach
            raw_html = request.form.get('contenido_html', '')
            # Permitir tags básicos de formato
            allowed_tags = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'br', 'span', 'div']
            allowed_attrs = {'*': ['class', 'style'], 'a': ['href', 'target']}
            clean_html = bleach.clean(raw_html, tags=allowed_tags, attributes=allowed_attrs)
            nueva_leccion.contenido = clean_html
            
        elif tipo_post in ['pdf', 'video', 'audio']:
            archivo = request.files.get('archivo')
            if not archivo or archivo.filename == '':
                flash('Debe seleccionar un archivo.', 'danger')
                return redirect(request.url)
                
            folder = f"lecciones/{curso.id}"
            object_name = minio_svc.upload_file(
                file_stream=archivo.stream,
                original_filename=archivo.filename,
                folder_path=folder,
                content_type=archivo.content_type
            )
            
            if object_name:
                nueva_leccion.contenido = object_name
            else:
                flash('Error al subir el archivo a MinIO.', 'danger')
                return redirect(request.url)
                
        try:
            db.session.add(nueva_leccion)
            db.session.commit()
            flash('Lección creada exitosamente.', 'success')
            return redirect(url_for('admin_cursos.builder', id=curso.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar la lección: {str(e)}', 'danger')

    modulos = Modulo.query.filter_by(curso_id=curso.id).order_by(Modulo.orden).all()
    return render_template('admin/cursos/leccion_form.html', curso=curso, modulos=modulos, modulo_id=modulo_id, tipo=tipo, leccion=None)

@admin_lecciones_bp.route('/lecciones/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    leccion = Leccion.query.get_or_404(id)
    curso = leccion.curso
    
    # Obtener URL actual si es archivo
    archivo_url = None
    if leccion.tipo in ['pdf', 'video', 'audio'] and leccion.contenido:
        archivo_url = minio_svc.get_file_url(leccion.contenido)
        
    if request.method == 'POST':
        leccion.titulo = request.form.get('titulo')
        leccion.duracion_min = request.form.get('duracion_min', type=int)
        
        mod_id = request.form.get('modulo_id', type=int)
        leccion.modulo_id = mod_id if mod_id else None
        
        if leccion.tipo == 'html':
            import bleach
            raw_html = request.form.get('contenido_html', '')
            allowed_tags = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'br', 'span', 'div']
            allowed_attrs = {'*': ['class', 'style'], 'a': ['href', 'target']}
            leccion.contenido = bleach.clean(raw_html, tags=allowed_tags, attributes=allowed_attrs)
            
        elif leccion.tipo in ['pdf', 'video', 'audio']:
            archivo = request.files.get('archivo')
            # Solo actualizar si se subió un nuevo archivo
            if archivo and archivo.filename != '':
                # Eliminar el viejo de MinIO
                if leccion.contenido:
                    minio_svc.delete_file(leccion.contenido)
                    
                folder = f"lecciones/{curso.id}"
                object_name = minio_svc.upload_file(
                    file_stream=archivo.stream,
                    original_filename=archivo.filename,
                    folder_path=folder,
                    content_type=archivo.content_type
                )
                if object_name:
                    leccion.contenido = object_name
                    
        try:
            db.session.commit()
            flash('Lección actualizada exitosamente.', 'success')
            return redirect(url_for('admin_cursos.builder', id=curso.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    modulos = Modulo.query.filter_by(curso_id=curso.id).order_by(Modulo.orden).all()
    return render_template('admin/cursos/leccion_form.html', curso=curso, modulos=modulos, tipo=leccion.tipo, leccion=leccion, archivo_url=archivo_url)

@admin_lecciones_bp.route('/lecciones/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar(id):
    leccion = Leccion.query.get_or_404(id)
    curso_id = leccion.curso_id
    
    if leccion.tipo in ['pdf', 'video', 'audio'] and leccion.contenido:
        minio_svc.delete_file(leccion.contenido)
        
    try:
        db.session.delete(leccion)
        db.session.commit()
        flash('Lección eliminada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar.', 'danger')
        
    return redirect(url_for('admin_cursos.builder', id=curso_id))
