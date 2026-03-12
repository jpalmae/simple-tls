from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.curso import Curso
from app.models.usuario import Usuario
from app.models.departamento import Departamento
from app.models.inscripcion import Inscripcion
from app.utils.decorators import admin_required
from app import db
from datetime import datetime

admin_inscripciones_bp = Blueprint('admin_inscripciones', __name__)


@admin_inscripciones_bp.route('/inscripciones')
@login_required
@admin_required
def index():
    """Vista principal: lista todas las inscripciones con filtros."""
    curso_id = request.args.get('curso_id', type=int)
    depto_id = request.args.get('departamento_id', type=int)
    estado = request.args.get('estado')

    query = Inscripcion.query

    if curso_id:
        query = query.filter_by(curso_id=curso_id)
    if estado:
        query = query.filter_by(estado=estado)
    if depto_id:
        query = query.join(Usuario, Inscripcion.usuario_id == Usuario.id).filter(Usuario.departamento_id == depto_id)

    inscripciones = query.order_by(Inscripcion.fecha_inscripcion.desc()).all()
    cursos = Curso.query.order_by(Curso.titulo).all()
    departamentos = Departamento.query.order_by(Departamento.nombre).all()

    return render_template(
        'admin/inscripciones/list.html',
        inscripciones=inscripciones,
        cursos=cursos,
        departamentos=departamentos,
        filtro_curso=curso_id,
        filtro_depto=depto_id,
        filtro_estado=estado
    )


@admin_inscripciones_bp.route('/inscripciones/asignar', methods=['GET', 'POST'])
@login_required
@admin_required
def asignar():
    """Formulario para asignar un curso a usuarios individuales o a un departamento completo."""
    cursos = Curso.query.filter_by(activo=True).order_by(Curso.titulo).all()
    departamentos = Departamento.query.order_by(Departamento.nombre).all()
    usuarios = Usuario.query.filter_by(activo=True).order_by(Usuario.apellido).all()

    if request.method == 'POST':
        curso_id = int(request.form.get('curso_id'))
        fecha_limite_str = request.form.get('fecha_limite')
        fecha_limite = datetime.strptime(fecha_limite_str, '%Y-%m-%d').date() if fecha_limite_str else None
        modo = request.form.get('modo')  # 'individual' or 'departamento'

        usuarios_a_inscribir = []

        if modo == 'departamento':
            depto_id = int(request.form.get('departamento_id'))
            usuarios_a_inscribir = Usuario.query.filter_by(departamento_id=depto_id, activo=True).all()
        elif modo == 'individual':
            ids = request.form.getlist('usuario_ids')
            usuarios_a_inscribir = Usuario.query.filter(Usuario.id.in_(ids)).all()

        count = 0
        for u in usuarios_a_inscribir:
            existe = Inscripcion.query.filter_by(usuario_id=u.id, curso_id=curso_id).first()
            if not existe:
                nueva = Inscripcion(
                    usuario_id=u.id,
                    curso_id=curso_id,
                    fecha_limite=fecha_limite,
                    asignado_por=current_user.id
                )
                db.session.add(nueva)
                count += 1

        db.session.commit()
        flash(f'Se inscribieron {count} usuario(s) exitosamente.', 'success')
        return redirect(url_for('admin_inscripciones.index', curso_id=curso_id))

    return render_template(
        'admin/inscripciones/asignar.html',
        cursos=cursos,
        departamentos=departamentos,
        usuarios=usuarios
    )


@admin_inscripciones_bp.route('/inscripciones/<int:inscripcion_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar(inscripcion_id):
    """Elimina (des-inscribe) a un usuario de un curso."""
    ins = Inscripcion.query.get_or_404(inscripcion_id)
    curso_id = ins.curso_id
    db.session.delete(ins)
    db.session.commit()
    flash('Inscripción eliminada correctamente.', 'success')
    return redirect(url_for('admin_inscripciones.index', curso_id=curso_id))


@admin_inscripciones_bp.route('/calendario')
@login_required
@admin_required
def calendario():
    """Vista de calendario mostrando las inscripciones con fecha_limite."""
    inscripciones = Inscripcion.query.filter(Inscripcion.fecha_limite.isnot(None)).all()

    eventos = []
    for ins in inscripciones:
        color = '#3b82f6'  # blue
        if ins.estado == 'aprobado':
            color = '#22c55e'
        elif ins.estado == 'reprobado':
            color = '#ef4444'
        elif ins.estado == 'vencido':
            color = '#9ca3af'

        eventos.append({
            'title': f'{ins.usuario.nombre} {ins.usuario.apellido} - {ins.curso.titulo}',
            'start': ins.fecha_limite.isoformat(),
            'color': color,
            'url': url_for('admin_inscripciones.index', curso_id=ins.curso_id)
        })

    return render_template('admin/inscripciones/calendario.html', eventos=eventos)
