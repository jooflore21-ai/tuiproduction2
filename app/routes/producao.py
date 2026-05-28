from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import models
from datetime import datetime

producao_bp = Blueprint('producao', __name__)


@producao_bp.route('/producao', methods=['GET', 'POST'])
def producao():
    # --- Lógica para lidar com o envio do formulário (POST) ---
    if request.method == 'POST':
        print(f"DEBUG: Dados recebidos do formulário: {request.form}")
        try:
            # Pega os dados comuns do formulário
            tipo_registro = request.form.get('tipo_registro')
            modelo_nome = request.form.get('modelo')
            # Converte quantidade para inteiro, tratando erro se não for número
            quantidade = int(request.form.get('quantidade'))
            cor_paralama = request.form.get('cor_paralama')
            edicao_id = request.form.get('edicao')

            if not tipo_registro or not modelo_nome or quantidade <= 0:
                flash('Erro: Todos os campos são obrigatórios e a quantidade deve ser positiva.', 'error')
                return redirect(url_for('producao'))

            # --- Ramo 1: Registro para ESTOQUE ---
            if tipo_registro == 'estoque':
                # Constrói o nome completo da variação
                cor_chassis = None
                nome_completo = modelo_nome
                if modelo_nome == 'TUI POP':
                    cor_chassis = request.form.get('cor_chassis')
                    cor_paralama = request.form.get('cor_paralama')
                    nome_completo = f"{modelo_nome} {cor_paralama}"
                elif modelo_nome in ['TUI', 'TUI MAIS']:
                    cor_paralama = request.form.get('cor_paralama')
                    nome_completo = f"{modelo_nome} {cor_paralama}"

                models.registrar_producao(modelo_nome=modelo_nome,
                    cor_paralama=cor_paralama,
                    cor_chassis=cor_chassis,
                    edicao_id=edicao_id,
                    quantidade=quantidade)

                # Baixa automática das peças da BOM
                # Só executa para TUI MAIS e TUI POP (modelos com BOM cadastrada)
                if modelo_nome in ('TUI MAIS', 'TUI POP'):
                    models.baixar_estoque_por_bom(
                        modelo=modelo_nome,
                        cor_scooter=cor_paralama,
                        quantidade_scooters=quantidade
                    )

                nome_completo = f"{modelo_nome} {cor_paralama}"
                flash(f"Produção de {quantidade}x '{nome_completo}' registrada com sucesso!", 'success')

            # --- Ramo 2: Registro para ASSISTÊNCIA ---
            elif tipo_registro == 'assistencia':
                # Para assistência, usamos apenas o nome do modelo_nome
                models.registrar_assistencia(modelo_nome, quantidade)
                flash(f'{quantidade} unidade(s) de "{modelo_nome}" registrada(s) para assistência com sucesso!', 'success')

        except ValueError as e:
            # Captura erros de conversão de número ou de produto não encontrado
            flash(f'Erro ao registrar: {e}', 'error')
        except Exception as e:
            # Captura outros erros inesperados
            flash(f'Ocorreu um erro inesperado: {e}', 'error')

        return redirect(url_for('producao', **request.args))

    # --- Lógica para exibir a página (GET) ---
    # Busca os dados para exibir nas tabelas do painel
    producao_diaria = models.consultar_producao(periodo="diario")
    assistencia_diaria = models.consultar_assistencia(periodo="diario")
    estoque_atual = models.consultar_estoque()
    estoque_por_modelo = models.consultar_estoque_por_modelo()

    # --- Filtra o período selecionado via URL ---
    periodo_selecionado = request.args.get('periodo', 'diario')

    mes_especifico = request.args.get('mes_filtro')
    periodo_padrao = request.args.get('periodo')

    if mes_especifico:
        periodo_selecionado = mes_especifico
    elif periodo_padrao:
        periodo_selecionado = periodo_padrao
    else:
        periodo_selecionado = 'diario'

    # --- Lê a aba ativa da URL. O padrão é 'visao-geral' ---
    aba_ativa = request.args.get('aba', 'visao-geral')

    producao_lista = models.consultar_producao(periodo=periodo_selecionado)
    assistencia_lista = models.consultar_assistencia(periodo=periodo_selecionado)

    estoque_detalhado = models.consultar_estoque()

    edicoes = models.listar_edicoes()

    # --- Formata a data para cada item ---
    for item in producao_lista:
        dt_obj = datetime.strptime(item['data_hora'], '%Y-%m-%d %H:%M:%S')
        item['dia'] = dt_obj.strftime('%d/%m')
        item['hora'] = dt_obj.strftime('%H:%M')

    for item in assistencia_lista:
        dt_obj = datetime.strptime(item['data_hora'], '%Y-%m-%d %H:%M:%S')
        item['dia'] = dt_obj.strftime('%d/%m')
        item['hora'] = dt_obj.strftime('%H:%M')

    # Dados para popular os dropdowns do formulário
    form_data = {
        'modelos': ["TUI MAIS", "TUI POP"],
        'cores_paralama': ["BRANCO", "PRETO", "VERMELHO", "CINZA", "AZUL", "AMARELO", "BRONZE", "PRATA", "LARANJA", "ROSA", "ROXO", "VERDE"],
        'cores_chassis': ["PRETO"],
        'cores_css': {
            "AMARELO": "#f1c40f",
            "CINZA": "#4d4d4d",
            "AZUL": "#000099",
            "BRANCO": "#ecf0f1",
            "BRONZE": "#a75d25",
            "LARANJA": "#F25C05",
            "PRATA": "#bdc3c7",
            "PRETO": "#000000",
            "ROSA": "#ff79c6",
            "ROXO": "#592f6a",
            "VERDE": "#00ff00",
            "VERMELHO": "#d60202"
        }
    }

    # Renderiza o template, passando todas as informações necessárias
    return render_template(
        'producao.html',
        producao_diaria=producao_lista,
        assistencia_diaria=assistencia_lista,
        estoque_atual=models.consultar_estoque(),
        estoque_por_modelo=models.consultar_estoque_por_modelo(),
        estoque_detalhado=estoque_detalhado,
        form_data=form_data,
        periodo_selecionado=periodo_selecionado,
        aba_ativa=aba_ativa,
        edicoes=edicoes
    )


@producao_bp.route('/producao/excluir/<int:id_producao>', methods=['POST'])
def excluir_producao(id_producao):
    try:
        models.deletar_producao(id_producao)
        flash('Registro de produção excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir registro: {e}', 'error')
    return redirect(url_for('producao'))


@producao_bp.route('/assistencia/excluir/<int:id_assistencia>', methods=['POST'])
def excluir_assistencia(id_assistencia):
    try:
        models.deletar_assistencia(id_assistencia)
        flash('Registro de assistência excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir registro: {e}', 'error')
    return redirect(url_for('producao'))


@producao_bp.route('/producao/editar/<int:id_producao>', methods=['POST'])
def editar_producao(id_producao):
    try:
        nova_quantidade = int(request.form.get('quantidade'))
        nova_data = request.form.get('nova_data')

        if nova_quantidade <= 0:
            raise ValueError("A quantidade deve ser positiva.")
        models.atualizar_producao(id_producao, nova_quantidade, nova_data)
        flash('Registro de produção atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar registro: {e}', 'error')
    return redirect(url_for('producao'))


@producao_bp.route('/assistencia/editar/<int:id_assistencia>', methods=['POST'])
def editar_assistencia(id_assistencia):
    try:
        nova_quantidade = int(request.form.get('quantidade'))
        if nova_quantidade <= 0:
            raise ValueError("A quantidade deve ser positiva.")
        models.atualizar_assistencia(id_assistencia, nova_quantidade)
        flash('Registro de assistência atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar registro: {e}', 'error')
    return redirect(url_for('producao'))


@producao_bp.route('/edicoes/nova', methods=['POST'])
def nova_edicao():
    nome_edicao = request.json.get('nome')
    if not nome_edicao:
        return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400

    try:
        novo_id = models.criar_edicao(nome_edicao)
        return jsonify({'success': True, 'id': novo_id, 'nome': nome_edicao})
    except Exception as e:
        # Trata o caso de o nome já existir (UNIQUE constraint)
        return jsonify({'success': False, 'error': str(e)}), 500
