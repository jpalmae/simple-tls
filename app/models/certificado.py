from datetime import datetime, timezone
from app import db

class Certificado(db.Model):
    __tablename__ = 'certificados'

    id = db.Column(db.Integer, primary_key=True)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey('inscripciones.id'), nullable=False)
    intento_id = db.Column(db.Integer, db.ForeignKey('intentos.id'), nullable=False)
    url_archivo = db.Column(db.Text, nullable=False)
    fecha_emision = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
