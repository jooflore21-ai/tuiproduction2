from flask import Blueprint, render_template
from app import models
from datetime import datetime

estoque_bp = Blueprint('estoque', __name__)


@estoque_bp.route('/estoque_geral')
def estoque_geral():

    # ── Painel de scooters (lógica existente — não alterar) ──────────────────
    estoque_cru = models.consultar_estoque()
    painel = {"TUI MAIS": {}, "TUI POP": {}, "Outros": {}}

    for item in estoque_cru:
        nome_completo = item['nome_completo']
        qtd           = item['estoque_atual']
        edicao_id     = item.get('edicao_id', 1)
        edicao_nome   = item.get('edicao_nome', 'Padrão')

        if edicao_id != 1:
            modelo = "Outros"
            cor    = f"{nome_completo} [{edicao_nome}]"
        elif nome_completo.startswith("TUI MAIS"):
            modelo = "TUI MAIS"
            cor    = nome_completo.replace("TUI MAIS ", "").strip()
        elif nome_completo.startswith("TUI POP"):
            modelo = "TUI POP"
            cor    = nome_completo.replace("TUI POP ", "").strip()
        else:
            modelo = "Outros"
            cor    = nome_completo

        painel[modelo][cor] = qtd

    painel = {k: v for k, v in painel.items() if v}

    # ── KPIs ─────────────────────────────────────────────────────────────────
    total_scooters = sum(sum(cores.values()) for cores in painel.values())

    pecas_criticas = models.consultar_pecas_criticas(minimo=20)
    total_criticas = len(pecas_criticas)

    defeitos_mes   = models.consultar_defeitos_para_relatorio()
    total_defeitos = sum(d['quantidade'] for d in defeitos_mes)

    producao_hoje  = models.consultar_producao(periodo='diario')
    embaladas_hoje = sum(p['quantidade'] for p in producao_hoje)

    # ── Variação mais embalada (últimos 30 dias) ──────────────────────────────
    producao_30d   = models.consultar_producao(periodo='ultimos_30_dias')
    contagem_cores = {}
    for p in producao_30d:
        partes = p['nome_completo'].split()
        cor    = partes[-1] if partes else 'DESCONHECIDA'
        contagem_cores[cor] = contagem_cores.get(cor, 0) + p['quantidade']

    top_cores = sorted(
        contagem_cores.items(), key=lambda x: x[1], reverse=True
    )[:11]

    # ── Defeitos por peça (acumulado) ────────────────────────────────────────
    defeitos_por_peca = {}
    for d in defeitos_mes:
        nome = d['nome']
        defeitos_por_peca[nome] = defeitos_por_peca.get(nome, 0) + d['quantidade']

    top_defeitos = sorted(
        defeitos_por_peca.items(), key=lambda x: x[1], reverse=True
    )[:5]

    # ── Tendência semanal ─────────────────────────────────────────────────────
    # Usa ultimos_30_dias como proxy (período disponível no model)
    producao_90d = models.consultar_producao(periodo='ultimos_30_dias')

    semanas_mais = {}
    semanas_pop  = {}
    for p in producao_90d:
        try:
            dt  = datetime.strptime(p['data_hora'], '%Y-%m-%d %H:%M:%S')
            sem = dt.strftime('%Y-W%W')
        except Exception:
            continue
        nome = p['nome_completo']
        if 'MAIS' in nome:
            semanas_mais[sem] = semanas_mais.get(sem, 0) + p['quantidade']
        elif 'POP' in nome:
            semanas_pop[sem]  = semanas_pop.get(sem, 0)  + p['quantidade']

    todas_semanas = sorted(
        set(list(semanas_mais.keys()) + list(semanas_pop.keys()))
    )
    trend_labels = todas_semanas[-12:]
    trend_mais   = [semanas_mais.get(s, 0) for s in trend_labels]
    trend_pop    = [semanas_pop.get(s, 0)  for s in trend_labels]

    return render_template(
        'estoque_geral.html',
        painel=painel,
        cores_css=models.CORES_CSS,
        # KPIs
        total_scooters=total_scooters,
        total_criticas=total_criticas,
        total_defeitos=total_defeitos,
        embaladas_hoje=embaladas_hoje,
        # Gráficos
        top_cores=top_cores,
        top_defeitos=top_defeitos,
        pecas_criticas=pecas_criticas[:7],
        trend_labels=trend_labels,
        trend_mais=trend_mais,
        trend_pop=trend_pop,
    )
