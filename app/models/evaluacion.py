from app import db

class Evaluacion(db.Model):
    __tablename__ = 'evaluaciones'

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    instrucciones = db.Column(db.Text, nullable=True)
    nota_minima_aprobacion = db.Column(db.Integer, nullable=False, default=60)
    intentos_maximos = db.Column(db.Integer, nullable=False, default=3)
    tiempo_limite_min = db.Column(db.Integer, nullable=True)
    aleatorizar_preguntas = db.Column(db.Boolean, default=False)
    aleatorizar_opciones = db.Column(db.Boolean, default=False)
    mostrar_respuestas_correctas_al_final = db.Column(db.Boolean, default=True)

    # Relaciones
    preguntas = db.relationship('Pregunta', backref='evaluacion', lazy='dynamic', cascade='all, delete-orphan')
    intentos = db.relationship('Intento', backref='evaluacion_intentos', lazy='dynamic', cascade='all, delete-orphan')


class Pregunta(db.Model):
    __tablename__ = 'preguntas'

    id = db.Column(db.Integer, primary_key=True)
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluaciones.id'), nullable=False)
    enunciado = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.Enum('multiple', 'verdadero_falso', name='tipos_pregunta'), nullable=False)
    puntaje = db.Column(db.Integer, nullable=False, default=1)
    orden = db.Column(db.Integer, nullable=False, default=1)

    # Relaciones
    opciones = db.relationship('Opcion', backref='pregunta', lazy='dynamic', cascade='all, delete-orphan')


class Opcion(db.Model):
    __tablename__ = 'opciones'

    id = db.Column(db.Integer, primary_key=True)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('preguntas.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    es_correcta = db.Column(db.Boolean, default=False)
