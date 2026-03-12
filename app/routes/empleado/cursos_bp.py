from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.curso import Curso
from app.models.inscripcion import Inscripcion, ProgresoLeccion
from app import db, minio_svc
from datetime import datetime

empleado_cursos_bp = Blueprint('empleado_cursos', __name__)

@empleado_cursos_bp.route('/')
@login_required
def dashboard():
    """Muestra los cursos en los que el usuario está inscrito."""
    # Obtener inscripciones activas del usuario
    inscripciones = Inscripcion.query.filter_by(usuario_id=current_user.id).all()
    
    cursos_enriquecidos = []
    
    for ins in inscripciones:
        curso = ins.curso
        if not curso.activo:
            continue
            
        # Calcular progreso
        total_lecciones = curso.lecciones.count()
        lecciones_completadas = ProgresoLeccion.query.filter_by(
            inscripcion_id=ins.id,
            completada=True
        ).count()
        
        porcentaje = int((lecciones_completadas / total_lecciones) * 100) if total_lecciones > 0 else 0
        
        # Obtener URL firmada de la portada
        cover_url = minio_svc.get_file_url(curso.imagen_portada_url) if curso.imagen_portada_url else None
        
        cursos_enriquecidos.append({
            'curso': curso,
            'inscripcion': ins,
            'cover_url': cover_url,
            'progreso_porcentaje': porcentaje,
            'lecciones_completadas': lecciones_completadas,
            'total_lecciones': total_lecciones
        })
        
    return render_template('empleado/dashboard.html', cursos_inscritos=cursos_enriquecidos)

@empleado_cursos_bp.route('/<int:id>')
@login_required
def detalle(id):
    """Muestra el syllabus del curso y el progreso por lección."""
    curso = Curso.query.get_or_404(id)
    
    # Verificar inscripción (o permitir acceso si es admin para pruebas)
    inscripcion = Inscripcion.query.filter_by(usuario_id=current_user.id, curso_id=curso.id).first()
    
    if not inscripcion and current_user.rol != 'admin':
        flash('No estás inscrito en este curso o el acceso ha sido revocado.', 'warning')
        return redirect(url_for('empleado_cursos.dashboard'))
        
    # Obtener progreso del usuario para este curso en un dict {leccion_id: ProgresoLeccion}
    progresos_raw = ProgresoLeccion.query.filter_by(inscripcion_id=inscripcion.id).all() if inscripcion else []
    progreso_dict = {p.leccion_id: p for p in progresos_raw}
    
    cover_url = minio_svc.get_file_url(curso.imagen_portada_url) if curso.imagen_portada_url else None

    # Lógica para determinar qué lecciones están "bloqueadas" si el curso es secuencial
    lecciones_ordenadas = curso.lecciones.order_by('orden').all()
    lecciones_estado = [] # lista de dicts con info enriquecida
    
    bloqueado_siguiente = False
    
    for leccion in lecciones_ordenadas:
        estado = {
            'leccion': leccion,
            'completada': False,
            'bloqueada': False,
            'ultima_fecha': None
        }
        
        prog = progreso_dict.get(leccion.id)
        if prog and prog.completada:
            estado['completada'] = True
            estado['ultima_fecha'] = prog.fecha_completado
            
        if curso.secuencial:
            if bloqueado_siguiente:
                estado['bloqueada'] = True
            
            # Si esta lección actual NO está completada, la SIGUIENTE estará bloqueada
            if not estado['completada']:
                bloqueado_siguiente = True
        
        lecciones_estado.append(estado)

    return render_template('empleado/curso_detalle.html', 
                          curso=curso, 
                          inscripcion=inscripcion, 
                          cover_url=cover_url,
                          lecciones_estado=lecciones_estado)

@empleado_cursos_bp.route('/<int:id>/debug-inscribir', methods=['POST'])
@login_required
def debug_inscribir(id):
    """Ruta temporal para autoinscribirse con fines de prueba (Fase 4)."""
    curso = Curso.query.get_or_404(id)
    
    existente = Inscripcion.query.filter_by(usuario_id=current_user.id, curso_id=curso.id).first()
    if not existente:
        nueva_ins = Inscripcion(
            usuario_id=current_user.id,
            curso_id=curso.id,
            fecha_inscripcion=datetime.utcnow()
        )
        db.session.add(nueva_ins)
        try:
            db.session.commit()
            flash(f'Te has inscrito exitosamente de forma manual a "{curso.titulo}".', 'success')
        except:
            db.session.rollback()
            flash('Error al generar la inscripción de prueba.', 'danger')
    else:
        flash('Ya estás inscrito en este curso.', 'info')
        
    return redirect(url_for('empleado_cursos.dashboard'))
