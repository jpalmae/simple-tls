from app import create_app, db, bcrypt
from app.models.usuario import Usuario

app = create_app()

with app.app_context():
    # Revisar si ya existe el admin
    admin = Usuario.query.filter_by(email='admin@sixmanager.cl').first()
    if not admin:
        password = "SixManager2026!"
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        nuevo_admin = Usuario(
            nombre='Admin',
            apellido='Sistema',
            email='admin@sixmanager.cl',
            password_hash=password_hash,
            rol='admin',
            activo=True
        )
        
        db.session.add(nuevo_admin)
        db.session.commit()
        print("Usuario administrador creado:")
        print("Email: admin@sixmanager.cl")
        print(f"Password: {password}")
    else:
        print("El usuario administrador ya existe.")
