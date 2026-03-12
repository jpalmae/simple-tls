from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app.models.curso import Leccion, Curso
from app.models.inscripcion import Inscripcion, ProgresoLeccion
from app import db, minio_svc
from datetime import datetime

visor_bp = Blueprint('visor', __name__)

@visor_bp.route('/visor/leccion/<int:leccion_id>')
@login_required
def ver_leccion(leccion_id):
    """Muestra el reproductor del curso para una lección específica."""
    leccion = Leccion.query.get_or_404(leccion_id)
    curso = leccion.curso
    
    # Validar acceso
    inscripcion = Inscripcion.query.filter_by(usuario_id=current_user.id, curso_id=curso.id).first()
    if not inscripcion and current_user.rol != 'admin':
        abort(403) # Forbidden
        
    # Obtener historial de progreso de este usuario para TODO el curso para renderizar el menú lateral
    progresos_raw = ProgresoLeccion.query.filter_by(inscripcion_id=inscripcion.id).all() if inscripcion else []
    progreso_dict = {p.leccion_id: p for p in progresos_raw}
    
    # Lógica de secuencialidad (Sidebar y Prevención de acceso por URL directa)
    lecciones_ordenadas = curso.lecciones.order_by('orden').all()
    lecciones_estado = []
    
    bloqueado_siguiente = False
    leccion_actual_bloqueada = False
    
    indice_actual = 0
    leccion_anterior_id = None
    leccion_siguiente_id = None
    
    for i, lec in enumerate(lecciones_ordenadas):
        completada = True if (progreso_dict.get(lec.id) and progreso_dict[lec.id].completada) else False
        bloqueada = False
        
        if curso.secuencial and bloqueado_siguiente:
            bloqueada = True
            
        if lec.id == leccion.id:
            indice_actual = i
            leccion_actual_bloqueada = bloqueada
            if i > 0:
                leccion_anterior_id = lecciones_ordenadas[i-1].id
                
        # Calcular siguiente por adelantado para el loop 
        # (se actualizará correctamente en la siguiente pasada si existe)
            
        if curso.secuencial and not completada:
            bloqueado_siguiente = True
            
        lecciones_estado.append({
            'id': lec.id,
            'titulo': lec.titulo,
            'modulo_id': lec.modulo_id,
            'tipo': lec.tipo,
            'completada': completada,
            'bloqueada': bloqueada
        })

    if indice_actual < len(lecciones_ordenadas) - 1:
        siguiente = lecciones_ordenadas[indice_actual+1]
        # Verificar si la siguiente está bloqueada para no mostrar el botón
        siguiente_estado = next((e for e in lecciones_estado if e['id'] == siguiente.id), None)
        if not siguiente_estado or not siguiente_estado['bloqueada']:
             leccion_siguiente_id = siguiente.id

    if leccion_actual_bloqueada and current_user.rol != 'admin':
        # Intento de saltarse la secuencia escribiendo la URL manual
        return render_template('empleado/error_secuencia.html', curso=curso), 403
        
    # Obtener la URL del archivo multimedia en MinIO si aplica
    contenido_url = None
    if leccion.tipo in ['pdf', 'video', 'audio'] and leccion.contenido:
        contenido_url = minio_svc.get_file_url(leccion.contenido)

    # Registrar el acceso inicial (en progreso, no completado aún)
    prog_actual = progreso_dict.get(leccion.id)
    if not prog_actual and inscripcion:
        nuevo_progreso = ProgresoLeccion(
            inscripcion_id=inscripcion.id,
            leccion_id=leccion.id,
            completada=False
        )
        db.session.add(nuevo_progreso)
        try:
            db.session.commit()
        except:
            db.session.rollback()

    return render_template('empleado/visor.html', 
                           curso=curso, 
                           leccion_actual=leccion,
                           lecciones_estado=lecciones_estado,
                           contenido_url=contenido_url,
                           leccion_anterior_id=leccion_anterior_id,
                           leccion_siguiente_id=leccion_siguiente_id)


@visor_bp.route('/api/progreso/completar', methods=['POST'])
@login_required
def marcar_completado():
    """API Endpoint llamado vía fetch/AJAX para marcar una lección como completada."""
    data = request.get_json()
    leccion_id = data.get('leccion_id')
    tiempo_visto = data.get('tiempo_visto_seg', 0)
    
    if not leccion_id:
        return jsonify({'error': 'Falta ID de lección'}), 400
        
    leccion = Leccion.query.get_or_404(leccion_id)
    
    # Validar que pertenece (simple check)
    inscripcion = Inscripcion.query.filter_by(usuario_id=current_user.id, curso_id=leccion.curso_id).first()
    if not inscripcion and current_user.rol != 'admin':
         return jsonify({'error': 'No autorizado'}), 403
         
    progreso = ProgresoLeccion.query.filter_by(inscripcion_id=inscripcion.id, leccion_id=leccion_id).first()
    
    try:
        if progreso:
            progreso.completada = True
            progreso.fecha_completado = datetime.utcnow()
        else:
            nuevo_progreso = ProgresoLeccion(
                inscripcion_id=inscripcion.id,
                leccion_id=leccion_id,
                completada=True,
                fecha_completado=datetime.utcnow()
            )
            db.session.add(nuevo_progreso)
            
        db.session.commit()
        
        # Opcional: Revisar si era la última lección y si hay evaluación para marcar el curso como completado
        # Esto se abordará a fondo en la Fase 5/6.
            
        return jsonify({'success': True, 'mensaje': 'Lección completada'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
