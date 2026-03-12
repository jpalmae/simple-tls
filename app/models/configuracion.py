from app import db

class Configuracion(db.Model):
    __tablename__ = 'configuracion'

    id = db.Column(db.Integer, primary_key=True)
    umbral_global_porcentaje = db.Column(db.Integer, nullable=False, default=80)
    dias_recordatorio_1 = db.Column(db.Integer, nullable=False, default=7)
    dias_recordatorio_2 = db.Column(db.Integer, nullable=False, default=3)
    dias_recordatorio_3 = db.Column(db.Integer, nullable=False, default=1)
    incluir_vencidos_en_denominador = db.Column(db.Boolean, nullable=False, default=True)
    nombre_app = db.Column(db.String(100), nullable=False, default='SixManager LMS')
    dominio = db.Column(db.String(255), nullable=False, default='localhost')
    logo_url = db.Column(db.Text, nullable=True)
    favicon_url = db.Column(db.Text, nullable=True)
