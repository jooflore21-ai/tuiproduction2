from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import models

pecas_bp = Blueprint('pecas', __name__)

CORES_PARALAMA = [
    'AMARELO', 'AZUL', 'BRANCO', 'BRONZE', 'CINZA',
    'LARANJA', 'PRATA', 'PRETO', 'ROSA', 'ROXO', 'VERDE', 'VERMELHO',
]


@pecas_bp.route('/pecas')
def listar_pecas():
    """Lista todas as peças raiz com estoque atual."""
    pecas = models.listar_pecas(apenas_ativas=True, apenas_raiz=True)
    pecas_criticas_count = len(models.consultar_pecas_criticas(minimo=20))
    return render_template('pecas/index.html', pecas=pecas,
                           pecas_criticas_count=pecas_criticas_count)


@pecas_bp.route('/pecas/nova', methods=['GET', 'POST'])
def nova_peca():
    """Formulário para adicionar nova peça."""
    if request.method == 'POST':
        try:
            codigo          = request.form.get('codigo', '').strip().upper()
            nome            = request.form.get('nome', '').strip()
            origem          = request.form.get('origem')
            container_tipo  = request.form.get('container_tipo', 'PADRAO')
            tem_variacao_cor = request.form.get('tem_variacao_cor') == 'on'
            peca_pai_id     = request.form.get('peca_pai_id') or None
            if peca_pai_id:
                peca_pai_id = int(peca_pai_id)

            if not codigo or not nome or not origem:
                flash('Código, nome e origem são obrigatórios.', 'error')
                return redirect(url_for('nova_peca'))

            models.adicionar_peca(
                codigo=codigo,
                nome=nome,
                origem=origem,
                container_tipo=container_tipo,
                tem_variacao_cor=tem_variacao_cor,
                peca_pai_id=peca_pai_id,
            )
            flash(f"Peça '{codigo} — {nome}' adicionada com sucesso!", 'success')
            return redirect(url_for('pecas'))

        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash(f'Erro inesperado: {e}', 'error')

        return redirect(url_for('nova_peca'))

    pecas_raiz = models.listar_pecas(apenas_ativas=True, apenas_raiz=True)
    return render_template('pecas/nova.html', pecas_raiz=pecas_raiz)


@pecas_bp.route('/pecas/<int:peca_id>/entrada', methods=['POST'])
def entrada_peca(peca_id):
    """Registra entrada de estoque para uma peça."""
    try:
        quantidade     = int(request.form.get('quantidade', 0))
        cor            = request.form.get('cor', '').strip() or None
        num_lote       = request.form.get('num_lote', '').strip()
        motivo_detalhe = request.form.get('motivo_detalhe', '').strip()

        if quantidade <= 0:
            raise ValueError("Quantidade deve ser positiva.")

        models.entrada_estoque_peca(
            peca_id=peca_id,
            quantidade=quantidade,
            cor=cor,
            num_lote=num_lote,
            motivo_detalhe=motivo_detalhe,
        )
        flash('Entrada registrada com sucesso!', 'success')

    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro inesperado: {e}', 'error')

    return redirect(url_for('pecas'))


@pecas_bp.route('/pecas/<int:peca_id>/saida', methods=['POST'])
def saida_peca(peca_id):
    """Registra saída manual (VENDA ou DEFEITO) de estoque."""
    try:
        quantidade     = int(request.form.get('quantidade', 0))
        tipo           = request.form.get('tipo', '').upper()
        cor            = request.form.get('cor', '').strip() or None
        num_pedido     = request.form.get('num_pedido', '').strip()
        motivo_detalhe = request.form.get('motivo_detalhe', '').strip()
        num_lote       = request.form.get('num_lote', '').strip()

        if quantidade <= 0:
            raise ValueError("Quantidade deve ser positiva.")
        if tipo not in ('VENDA', 'DEFEITO', 'ASSISTENCIA'):
            raise ValueError("Tipo deve ser VENDA, DEFEITO ou ASSISTENCIA.")

        models.saida_manual_peca(
            peca_id=peca_id,
            quantidade=quantidade,
            tipo=tipo,
            cor=cor,
            num_pedido=num_pedido,
            motivo_detalhe=motivo_detalhe,
            num_lote=num_lote,
        )
        flash(f"Saída de {quantidade}x peça registrada com sucesso!", 'success')

    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro inesperado: {e}', 'error')

    return redirect(url_for('pecas.listar_pecas'))


@pecas_bp.route('/pecas/movimentacoes')
def movimentacoes():
    """Log de movimentações com filtros."""
    peca_id_filtro = request.args.get('peca_id', '').strip()
    tipo_filtro    = request.args.get('tipo', '').strip()
    data_inicio    = request.args.get('data_inicio', '').strip()
    data_fim       = request.args.get('data_fim', '').strip()

    mov = models.consultar_movimentacoes(
        peca_id    = int(peca_id_filtro) if peca_id_filtro else None,
        tipo       = tipo_filtro or None,
        data_inicio= data_inicio or None,
        data_fim   = data_fim or None,
    )

    pecas_lista = models.listar_pecas(apenas_ativas=True)

    return render_template(
        'pecas/movimentacoes.html',
        movimentacoes=mov,
        pecas_lista=pecas_lista,
        peca_id_filtro=peca_id_filtro,
        tipo_filtro=tipo_filtro,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@pecas_bp.route('/pecas/criticas')
def criticas():
    """Retorna JSON com peças em estoque crítico (< 20)."""
    minimo = int(request.args.get('minimo', 20))
    pecas_crit = models.consultar_pecas_criticas(minimo=minimo)
    return jsonify({'pecas': pecas_crit})


@pecas_bp.route('/pecas/defeitos')
def defeitos():
    """Relatório de defeitos para reclamação ao fornecedor."""
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim    = request.args.get('data_fim', '').strip()

    registros = models.consultar_defeitos_para_relatorio(
        data_inicio=data_inicio or None,
        data_fim   =data_fim    or None,
    )

    return render_template(
        'pecas/defeitos.html',
        defeitos=registros,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@pecas_bp.route('/pecas/saida-lote', methods=['POST'])
def saida_peca_lote():
    """
    Recebe um JSON com múltiplos itens e registra cada um.
    Body esperado:
    {
        "num_pedido": "16543",
        "tipo": "VENDA",
        "motivo_detalhe": "...",
        "itens": [
            {"peca_id": 1, "quantidade": 4, "cor": null, "num_lote": ""},
            {"peca_id": 5, "quantidade": 2, "cor": "BRANCO", "num_lote": ""},
        ]
    }
    Retorna JSON: {"success": true} ou {"success": false, "error": "..."}
    Se qualquer item falhar, NENHUM é persistido (rollback manual).
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Payload inválido'}), 400

    num_pedido     = str(data.get('num_pedido', '')).strip()
    tipo           = str(data.get('tipo', '')).upper()
    motivo_detalhe = str(data.get('motivo_detalhe', '')).strip()
    itens          = data.get('itens', [])

    if tipo not in ('VENDA', 'DEFEITO', 'ASSISTENCIA'):
        return jsonify({'success': False, 'error': 'Tipo inválido'}), 400
    if not itens:
        return jsonify({'success': False, 'error': 'Nenhum item informado'}), 400

    erros = []
    for item in itens:
        try:
            peca_id  = int(item['peca_id'])
            qtd      = int(item['quantidade'])
            cor      = item.get('cor') or None
            num_lote = str(item.get('num_lote', '')).strip()

            if qtd <= 0:
                raise ValueError(f"Quantidade inválida para peça {peca_id}")

            models.saida_manual_peca(
                peca_id=peca_id,
                quantidade=qtd,
                tipo=tipo,
                cor=cor,
                num_pedido=num_pedido,
                motivo_detalhe=motivo_detalhe,
                num_lote=num_lote,
            )
        except ValueError as e:
            erros.append(str(e))
        except Exception as e:
            erros.append(f"Erro peça {item.get('peca_id')}: {e}")

    if erros:
        return jsonify({'success': False, 'error': '; '.join(erros)}), 422

    return jsonify({'success': True, 'itens_registrados': len(itens)})
