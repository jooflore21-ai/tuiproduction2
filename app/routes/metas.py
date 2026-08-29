from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app import models
from app.auth import admin_required

metas_bp = Blueprint('metas', __name__)


@metas_bp.route('/metas')
def painel_metas():
    dados = models.montar_dados_painel()
    return render_template('metas.html', dados=dados)


@metas_bp.route('/metas/dados')
def dados_metas():
    return jsonify(models.montar_dados_painel())


@metas_bp.route('/metas/admin')
@admin_required
def admin_metas():
    metas = models.obter_metas_config()
    dados = models.montar_dados_painel()
    return render_template('metas_admin.html', metas=metas, dados=dados)


@metas_bp.route('/metas/config', methods=['POST'])
@admin_required
def config_metas():
    setor = request.form.get('setor', '').strip()
    try:
        meta_diaria = int(request.form.get('meta_diaria'))
        if meta_diaria < 0:
            raise ValueError('Meta diária não pode ser negativa.')
        models.atualizar_meta_diaria(setor, meta_diaria)
        flash(f'Meta diária de "{setor}" atualizada para {meta_diaria}.', 'success')
    except (TypeError, ValueError):
        flash('Meta diária inválida — informe um número inteiro maior ou igual a 0.', 'error')
    return redirect(url_for('metas.admin_metas'))
