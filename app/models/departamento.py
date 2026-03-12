from app import db

class Departamento(db.Model):
    __tablename__ = 'departamentos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    umbral_minimo_porcentaje = db.Column(db.Integer, nullable=True) # override global

    # Relaciones
    usuarios = db.relationship('Usuario', backref='departamento', lazy='dynamic')
