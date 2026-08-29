from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth import pin_valido

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin = request.form.get('pin', '').strip()
        if pin_valido(pin):
            session.permanent = True
            session['admin_autenticado'] = True
            flash('Acesso liberado.', 'success')
            return redirect(url_for('metas.admin_metas'))
        flash('PIN inválido.', 'error')
    return render_template('admin_login.html')


@admin_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('admin_autenticado', None)
    flash('Sessão encerrada.', 'success')
    return redirect(url_for('landing_page'))
