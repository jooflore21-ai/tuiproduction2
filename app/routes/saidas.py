from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import models
from datetime import datetime

saida_bp = Blueprint('saida', __name__)


def _get_turno(hora_str):
    """Retorna o turno com base na hora (HH:MM)."""
    try:
        h = int(hora_str.split(':')[0])
    except Exception:
        return ''
    if 6 <= h < 12:
        return 'Matutino'
    elif 12 <= h < 18:
        return 'Vespertino'
    else:
        return 'Noturno'


@saida_bp.route('/saidas', methods=['GET', 'POST'])
def saidas():
    if request.method == 'POST':
        try:
            motivo = request.form.get('motivo')
            modelo_nome = request.form.get('modelo')
            quantidade = int(request.form.get('quantidade'))
            num_pedido = request.form.get('num_pedido', '').strip()

            # Constrói o nome completo da variação (5 modelos).
            # Famílias MAIS (MAIS/MAIS-S/MAIS-LS) → só paralama.
            # Famílias POP (POP/POP-S) → chassis fixo PRETO + paralama.
            # Bate com carregar_variacoes_modelos_novos() e com producao.py.
            nome_completo = modelo_nome
            cor_paralama = request.form.get('cor_paralama')

            if modelo_nome in ('TUI POP', 'TUI POP-S'):
                cor_chassis = 'PRETO'  # chassis padrão para saídas
                nome_completo = f"{modelo_nome} {cor_chassis} {cor_paralama}"
            elif modelo_nome in ('TUI', 'TUI MAIS', 'TUI MAIS-S', 'TUI MAIS-LS'):
                nome_completo = f"{modelo_nome} {cor_paralama}"

            models.registrar_saida(nome_completo, quantidade, motivo, num_pedido=num_pedido)
            flash(f"Saída de {quantidade}x '{nome_completo}' registrada com sucesso!", 'success')

        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash(f'Ocorreu um erro inesperado: {e}', 'error')

        return redirect(url_for('saidas'))

    # --- GET ---
    periodo_selecionado = request.args.get('periodo', 'ultimos_30_dias')
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim = request.args.get('data_fim', '').strip()

    # Se há filtro de datas explícito, ignora periodo
    if data_inicio or data_fim:
        periodo_selecionado = None
        log_saidas_raw = models.consultar_saidas(
            data_inicio=data_inicio or None,
            data_fim=data_fim or None
        )
    else:
        log_saidas_raw = models.consultar_saidas(periodo=periodo_selecionado)

    # Agrupa por num_pedido (ordem de inserção = mais recente primeiro)
    pedidos = {}
    for item in log_saidas_raw:
        dt_obj = datetime.strptime(item['data_hora'], '%Y-%m-%d %H:%M:%S')
        hora = dt_obj.strftime('%H:%M')
        data = dt_obj.strftime('%d/%m/%Y')
        turno = _get_turno(hora)

        chave = item['num_pedido'] or 'S/N'

        if chave not in pedidos:
            pedidos[chave] = {
                'num_pedido': chave,
                'motivo': item['motivo'],
                'data': data,
                'turno': turno,
                'itens': []
            }

        pedidos[chave]['itens'].append({
            'id': item['id'],
            'nome_completo': item['nome_completo'],
            'quantidade': item['quantidade'],
            'hora': hora,
        })

    log_pedidos = list(pedidos.values())

    # Uma única query para todas as movimentações VENDA/DEFEITO
    # do período, depois distribui por pedido em memória
    todas_movs = models.consultar_movimentacoes(
        tipo=None, data_inicio=data_inicio or None,
        data_fim=data_fim or None
    )
    movs_por_pedido = {}
    for m in todas_movs:
        if m['tipo'] in ('VENDA', 'DEFEITO') and m['num_pedido']:
            movs_por_pedido.setdefault(m['num_pedido'], []).append(m)

    for pedido in log_pedidos:
        chave = pedido['num_pedido']
        pedido['itens_peca'] = movs_por_pedido.get(chave, []) \
            if chave != 'S/N' else []

    form_data = {
        'motivos': ["CLIENTE", "REVENDA", "FEIRA", "BONIFICADO"],
        'modelos': ["TUI POP", "TUI MAIS", "TUI POP-S",
                    "TUI MAIS-S", "TUI MAIS-LS"],
        'cores_paralama': ["BRANCO", "PRETO", "VERMELHO", "CINZA", "AZUL", "AMARELO", "BRONZE", "PRATA", "LARANJA", "ROSA", "ROXO", "VERDE"],
        'cores_css': models.CORES_CSS,
    }

    pedidos_reservados = models.listar_pedidos_reservados()

    return render_template(
        'saidas.html',
        log_pedidos=log_pedidos,
        form_data=form_data,
        periodo_selecionado=periodo_selecionado,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pedidos_reservados=pedidos_reservados,
    )


@saida_bp.route('/saidas/excluir/<int:id_saida>', methods=['POST'])
def excluir_saida(id_saida):
    try:
        models.deletar_saida(id_saida)
        flash('Registro de saída excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir registro: {e}', 'error')
    return redirect(url_for('saidas'))


@saida_bp.route('/pedidos/<int:pedido_id>/despachar', methods=['POST'])
def despachar_pedido(pedido_id):
    motivo = request.form.get('motivo', '').strip().upper()
    MOTIVOS_VALIDOS = ['CLIENTE', 'REVENDA', 'FEIRA', 'BONIFICADO']
    if motivo not in MOTIVOS_VALIDOS:
        flash('Motivo inválido para despacho.', 'error')
        return redirect(url_for('saidas'))
    try:
        resultado = models.confirmar_despacho(pedido_id, motivo)
        flash(
            f"Pedido {resultado['num_pedido']} despachado com sucesso! "
            f"{resultado['itens_despachados']} item(s) registrado(s) "
            f"na saída.", 'success'
        )
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao despachar pedido: {e}', 'error')
    return redirect(url_for('saidas'))


@saida_bp.route('/saidas/editar/<int:id_saida>', methods=['POST'])
def editar_saida(id_saida):
    try:
        nova_quantidade = int(request.form.get('quantidade'))
        if nova_quantidade <= 0:
            raise ValueError("A quantidade deve ser positiva.")
        models.atualizar_saida(id_saida, nova_quantidade)
        flash('Registro de saída atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar registro: {e}', 'error')
    return redirect(url_for('saidas'))
