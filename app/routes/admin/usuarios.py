from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.models.usuario import Usuario
from app.models.departamento import Departamento
from app import db, bcrypt
import csv
import io

admin_users_bp = Blueprint('admin_users', __name__)

@admin_users_bp.route('/')
@login_required
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    usuarios = Usuario.query.paginate(page=page, per_page=20)
    return render_template('admin/usuarios_list.html', usuarios=usuarios)

@admin_users_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear():
    departamentos = Departamento.query.all()
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        rol = request.form.get('rol')
        departamento_id = request.form.get('departamento_id')
        
        # Generar contraseña por defecto
        password = "SixManager2026!"
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        nuevo_usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            email=email,
            password_hash=password_hash,
            rol=rol,
            departamento_id=departamento_id if departamento_id else None
        )
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash(f'Usuario {nombre} {apellido} creado exitosamente con contraseña por defecto: {password}', 'success')
            return redirect(url_for('admin_users.index'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear usuario. El email podría ya estar en uso.', 'danger')

    return render_template('admin/usuario_form.html', departamentos=departamentos, usuario=None)

@admin_users_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    departamentos = Departamento.query.all()
    
    if request.method == 'POST':
        usuario.nombre = request.form.get('nombre')
        usuario.apellido = request.form.get('apellido')
        usuario.email = request.form.get('email')
        usuario.rol = request.form.get('rol')
        
        dept_id = request.form.get('departamento_id')
        usuario.departamento_id = dept_id if dept_id else None
        
        activo_val = request.form.get('activo')
        usuario.activo = True if activo_val == 'on' else False
        
        try:
            db.session.commit()
            flash('Usuario actualizado correctamente.', 'success')
            return redirect(url_for('admin_users.index'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar usuario.', 'danger')
            
    return render_template('admin/usuario_form.html', departamentos=departamentos, usuario=usuario)

@admin_users_bp.route('/importar', methods=['POST'])
@login_required
@admin_required
def importar_csv():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('admin_users.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('admin_users.index'))

    if file and file.filename.endswith('.csv'):
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream, delimiter=',')
        
        created_count = 0
        error_count = 0
        password = "SixManager2026!"
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        for row in csv_input:
            email = row.get('email', '').strip()
            if not email:
                continue
                
            # Verificar si existe
            if Usuario.query.filter_by(email=email).first():
                error_count += 1
                continue
                
            # Buscar o crear departamento
            dept_nombre = row.get('departamento', '').strip()
            dept_id = None
            if dept_nombre:
                dept = Departamento.query.filter_by(nombre=dept_nombre).first()
                if not dept:
                    dept = Departamento(nombre=dept_nombre)
                    db.session.add(dept)
                    db.session.commit() # Commit para obtener ID
                dept_id = dept.id
            
            usuario = Usuario(
                nombre=row.get('nombre', '').strip(),
                apellido=row.get('apellido', '').strip(),
                email=email,
                password_hash=password_hash,
                rol=row.get('rol', 'empleado').strip().lower(),
                departamento_id=dept_id
            )
            db.session.add(usuario)
            created_count += 1
            
        try:
            db.session.commit()
            flash(f'Importación completada: {created_count} usuarios creados, {error_count} errores/duplicados.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error fatal durante la importación: {str(e)}', 'danger')
            
    else:
        flash('Por favor seleccione un archivo CSV.', 'warning')
        
    return redirect(url_for('admin_users.index'))
