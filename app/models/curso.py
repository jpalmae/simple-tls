from datetime import datetime, timezone
from app import db

class Curso(db.Model):
    __tablename__ = 'cursos'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    imagen_portada_url = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, default=False)
    secuencial = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    creado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Relaciones
    modulos = db.relationship('Modulo', backref='curso', lazy='dynamic', cascade='all, delete-orphan')
    lecciones = db.relationship('Leccion', backref='curso', lazy='dynamic', cascade='all, delete-orphan')
    evaluaciones = db.relationship('Evaluacion', backref='curso', lazy='dynamic', cascade='all, delete-orphan')
    inscripciones = db.relationship('Inscripcion', backref='curso', lazy='dynamic', cascade='all, delete-orphan')

class Modulo(db.Model):
    __tablename__ = 'modulos'

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    orden = db.Column(db.Integer, nullable=False, default=1)

    # Relaciones
    lecciones = db.relationship('Leccion', backref='modulo', lazy='dynamic', cascade='all, delete-orphan')


class Leccion(db.Model):
    __tablename__ = 'lecciones'

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)
    modulo_id = db.Column(db.Integer, db.ForeignKey('modulos.id'), nullable=True)
    titulo = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.Enum('html', 'pdf', 'video', 'audio', name='tipos_leccion'), nullable=False)
    contenido = db.Column(db.Text, nullable=False) # HTML content or MinIO URL depending on tipo
    duracion_min = db.Column(db.Integer, nullable=True)
    orden = db.Column(db.Integer, nullable=False, default=1)

    # Relaciones
    progresos = db.relationship('ProgresoLeccion', backref='leccion', lazy='dynamic', cascade='all, delete-orphan')
