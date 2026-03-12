import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address

# Initialize extensions (un-bound)
from flask_bcrypt import Bcrypt
from app.services.minio_service import MinioService

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
minio_svc = MinioService()
# limiter = Limiter(key_func=get_remote_address)

def create_app(config_name="default"):
    """Application factory definition."""
    app = Flask(__name__)
    
    # Use environment variable to determine config or use default
    env_config_name = os.environ.get("FLASK_ENV", config_name)
    from app.config import config
    app.config.from_object(config[env_config_name])
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    minio_svc.init_app(app)
    # limiter.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor inicie sesión para acceder a esta página."
    login_manager.login_message_category = "info"
    
    with app.app_context():
        # Import models here so Alembic can see them later
        from app import models
        
        # Configure user loader
        from app.services.auth_service import load_user
        login_manager.user_loader(load_user)

        # Register blueprints
        from app.routes.auth import auth_bp
        from app.routes.admin.usuarios import admin_users_bp
        from app.routes.admin.configuracion import admin_config_bp
        from app.routes.admin.cursos.cursos_bp import admin_cursos_bp
        from app.routes.admin.cursos.modulos_bp import admin_modulos_bp
        from app.routes.admin.cursos.lecciones_bp import admin_lecciones_bp
        from app.routes.admin.cursos.evaluaciones_bp import admin_evaluaciones_bp
        from app.routes.admin.inscripciones_bp import admin_inscripciones_bp
        from app.routes.empleado.cursos_bp import empleado_cursos_bp
        from app.routes.empleado.visor_bp import visor_bp
        from app.routes.empleado.evaluacion_bp import empleado_eval_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_users_bp, url_prefix='/admin/usuarios')
        app.register_blueprint(admin_config_bp, url_prefix='/admin/configuracion')
        app.register_blueprint(admin_cursos_bp, url_prefix='/admin/cursos')
        app.register_blueprint(admin_modulos_bp, url_prefix='/admin')
        app.register_blueprint(admin_lecciones_bp, url_prefix='/admin')
        app.register_blueprint(admin_evaluaciones_bp, url_prefix='/admin')
        app.register_blueprint(admin_inscripciones_bp, url_prefix='/admin')
        app.register_blueprint(empleado_cursos_bp, url_prefix='/mis-cursos')
        app.register_blueprint(empleado_eval_bp) # handles internal prefixes
        app.register_blueprint(visor_bp) # uses /visor prefix internally

        # API
        from app.routes.api.v1 import api_v1_bp
        app.register_blueprint(api_v1_bp, url_prefix='/api/v1')

        # Inject global config to all templates
        @app.context_processor
        def inject_config():
            from app.models.configuracion import Configuracion
            config = Configuracion.query.first()
            return dict(app_config=config, minio_svc=minio_svc)
        
    return app
