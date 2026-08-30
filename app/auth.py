import os
from functools import wraps

from dotenv import load_dotenv
from flask import flash, redirect, session, url_for

load_dotenv()


def pin_valido(pin):
    """Compara o PIN informado com ADMIN_PIN do .env. Único PIN compartilhado
    — não é sistema de usuários/papéis (decisão registrada em 27/08/2026)."""
    admin_pin = os.getenv('ADMIN_PIN')
    return bool(admin_pin) and pin == admin_pin


def admin_required(view_func):
    """Protege rotas que exigem sessão admin (session['admin_autenticado'])."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_autenticado'):
            flash('Acesso restrito.', 'error')
            return redirect(url_for('admin.login'))
        return view_func(*args, **kwargs)
    return wrapper
