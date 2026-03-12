from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.utils.decorators import admin_required
from app.models.configuracion import Configuracion
from app import db, minio_svc

admin_config_bp = Blueprint('admin_config', __name__)

@admin_config_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    # Obtener configuración (asumiendo que solo hay una fila, id=1)
    config = Configuracion.query.first()
    if not config:
        config = Configuracion()
        db.session.add(config)
        db.session.commit()

    if request.method == 'POST':
        config.umbral_global_porcentaje = int(request.form.get('umbral_global_porcentaje', 80))
        config.dias_recordatorio_1 = int(request.form.get('dias_recordatorio_1', 7))
        config.dias_recordatorio_2 = int(request.form.get('dias_recordatorio_2', 3))
        config.dias_recordatorio_3 = int(request.form.get('dias_recordatorio_3', 1))
        config.incluir_vencidos_en_denominador = True if request.form.get('incluir_vencidos') == 'on' else False
        
        config.nombre_app = request.form.get('nombre_app', 'SixManager LMS')
        config.dominio = request.form.get('dominio', 'localhost')
        
        # Subir logo si se envió un archivo
        logo_file = request.files.get('logo_file')
        if logo_file and logo_file.filename:
            if config.logo_url:
                minio_svc.delete_file(config.logo_url)
            config.logo_url = minio_svc.upload_file(logo_file, logo_file.filename, 'branding', logo_file.content_type)
        
        # Subir favicon si se envió un archivo
        favicon_file = request.files.get('favicon_file')
        if favicon_file and favicon_file.filename:
            if config.favicon_url:
                minio_svc.delete_file(config.favicon_url)
            config.favicon_url = minio_svc.upload_file(favicon_file, favicon_file.filename, 'branding', favicon_file.content_type)

        try:
            db.session.commit()
            flash('Configuración guardada exitosamente.', 'success')
            return redirect(url_for('admin_config.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar configuración: {str(e)}', 'danger')

    return render_template('admin/configuracion.html', config=config, minio_svc=minio_svc)
