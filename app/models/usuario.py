from datetime import datetime, timezone
from flask_login import UserMixin
from app import db

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('admin', 'empleado', name='roles_usuario'), nullable=False, default='empleado')
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamentos.id'), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ultimo_acceso = db.Column(db.DateTime, nullable=True)

    # Relaciones - creador de cursos, a quien se asignan las inscripciones
    cursos_creados = db.relationship('Curso', backref='creador', lazy='dynamic')
    inscripciones = db.relationship('Inscripcion', foreign_keys='Inscripcion.usuario_id', backref='usuario', lazy='dynamic')
    inscripciones_asignadas = db.relationship('Inscripcion', foreign_keys='Inscripcion.asignado_por', backref='asignador', lazy='dynamic')

    def is_active(self):
        return self.activo
