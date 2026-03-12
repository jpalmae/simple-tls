from datetime import datetime, timezone
from app import db

class Inscripcion(db.Model):
    __tablename__ = 'inscripciones'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_limite = db.Column(db.Date, nullable=True)
    estado = db.Column(db.Enum('pendiente', 'en_progreso', 'completado', 'aprobado', 'reprobado', 'vencido', name='estados_inscripcion'), nullable=False, default='pendiente')
    asignado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    # Relaciones
    progresos = db.relationship('ProgresoLeccion', backref='inscripcion', lazy='dynamic', cascade='all, delete-orphan')
    intentos = db.relationship('Intento', backref='inscripcion_intentos', lazy='dynamic', cascade='all, delete-orphan')
    certificados = db.relationship('Certificado', backref='inscripcion_cert', lazy='dynamic', cascade='all, delete-orphan')


class ProgresoLeccion(db.Model):
    __tablename__ = 'progreso_leccion'

    id = db.Column(db.Integer, primary_key=True)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey('inscripciones.id'), nullable=False)
    leccion_id = db.Column(db.Integer, db.ForeignKey('lecciones.id'), nullable=False)
    completada = db.Column(db.Boolean, default=False)
    fecha_completado = db.Column(db.DateTime, nullable=True)


class Intento(db.Model):
    __tablename__ = 'intentos'

    id = db.Column(db.Integer, primary_key=True)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey('inscripciones.id'), nullable=False)
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluaciones.id'), nullable=False)
    fecha_inicio = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_fin = db.Column(db.DateTime, nullable=True)
    puntaje_obtenido = db.Column(db.Integer, nullable=True)
    puntaje_maximo = db.Column(db.Integer, nullable=True)
    aprobado = db.Column(db.Boolean, nullable=True)

    # Relaciones
    respuestas = db.relationship('RespuestaIntento', backref='intento', lazy='dynamic', cascade='all, delete-orphan')
    certificados = db.relationship('Certificado', backref='intento_cert', lazy='dynamic')


class RespuestaIntento(db.Model):
    __tablename__ = 'respuestas_intento'

    id = db.Column(db.Integer, primary_key=True)
    intento_id = db.Column(db.Integer, db.ForeignKey('intentos.id'), nullable=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('preguntas.id'), nullable=False)
    opcion_id = db.Column(db.Integer, db.ForeignKey('opciones.id'), nullable=True) # Nullable si no respondió
