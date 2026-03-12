from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.usuario import Usuario
from app import bcrypt, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    """Redirige la raíz al dashboard o al login."""
    if current_user.is_authenticated:
        return redirect_dashboard()
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_dashboard()

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = Usuario.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return render_template('auth/login.html')
            
            login_user(user)
            user.ultimo_acceso = db.func.now()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect_dashboard()
        else:
            flash('Email o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))

def redirect_dashboard():
    if current_user.rol == 'admin':
        return redirect(url_for('admin_inscripciones.index'))
    return redirect(url_for('empleado_cursos.dashboard'))

