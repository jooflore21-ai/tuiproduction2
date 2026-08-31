from flask import Blueprint, render_template, request
from app import models
from datetime import datetime, date
import re

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

    pecas_criticas = models.consultar_pecas_criticas()
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

    # ── Comparativo de dois meses ────────────────────────────────────────────
    hoje = date.today()
    mes_atual_str = hoje.strftime('%Y-%m')
    if hoje.month == 1:
        mes_ant = hoje.replace(year=hoje.year - 1, month=12, day=1)
    else:
        mes_ant = hoje.replace(month=hoje.month - 1, day=1)
    mes_anterior_str = mes_ant.strftime('%Y-%m')

    mes_a = request.args.get('mes_a', mes_atual_str)     # mês de referência
    mes_b = request.args.get('mes_b', mes_anterior_str)  # mês de comparação

    if not re.match(r'^\d{4}-\d{2}$', mes_a):
        mes_a = mes_atual_str
    if not re.match(r'^\d{4}-\d{2}$', mes_b):
        mes_b = mes_anterior_str

    prod_a = models.consultar_producao(periodo=mes_a)
    prod_b = models.consultar_producao(periodo=mes_b)

    MODELOS_CONHECIDOS = [
        'TUI MAIS', 'TUI POP',
        'TUI MAIS-S', 'TUI POP-S', 'TUI MAIS-LS'
    ]

    def agregar_por_modelo(registros):
        """Soma quantidade por modelo. Ordena MODELOS_CONHECIDOS do mais
        específico ao mais genérico para não classificar 'TUI MAIS-S' como
        'TUI MAIS' via startswith."""
        totais = {m: 0 for m in MODELOS_CONHECIDOS}
        total_geral = 0
        modelos_por_especificidade = sorted(
            MODELOS_CONHECIDOS, key=len, reverse=True
        )
        for r in registros:
            nome = r['nome_completo']
            for modelo in modelos_por_especificidade:
                if nome.startswith(modelo):
                    totais[modelo] += r['quantidade']
                    total_geral += r['quantidade']
                    break
        return totais, total_geral

    totais_a, total_a = agregar_por_modelo(prod_a)
    totais_b, total_geral_b = agregar_por_modelo(prod_b)

    def calcular_delta(val_a, val_b):
        """Delta entre dois valores. Trata divisão por zero via 'tipo'."""
        unidades = val_a - val_b
        if val_b == 0 and val_a == 0:
            return {'unidades': 0, 'percentual': None, 'tipo': 'sem_dados'}
        if val_b == 0 and val_a > 0:
            return {'unidades': unidades, 'percentual': None, 'tipo': 'novo'}
        if val_a == 0 and val_b > 0:
            return {'unidades': unidades, 'percentual': -100.0, 'tipo': 'zerado'}
        pct = ((val_a - val_b) / val_b) * 100
        return {'unidades': unidades, 'percentual': round(pct, 1),
                'tipo': 'percentual'}

    delta_total = calcular_delta(total_a, total_geral_b)

    deltas_modelos = []
    for modelo in MODELOS_CONHECIDOS:
        d = calcular_delta(totais_a[modelo], totais_b[modelo])
        d['modelo'] = modelo
        d['val_a'] = totais_a[modelo]
        d['val_b'] = totais_b[modelo]
        deltas_modelos.append(d)

    def sort_key(d):
        """'novo' primeiro, depois por percentual absoluto desc,
        'sem_dados' sempre por último."""
        if d['tipo'] == 'sem_dados':
            return (-1, 0)
        if d['tipo'] == 'novo':
            return (1, d['val_a'])
        return (0, abs(d['percentual']))

    deltas_modelos.sort(key=sort_key, reverse=True)
    top2_modelos = deltas_modelos[:2]

    comp_labels = MODELOS_CONHECIDOS
    comp_data_a = [totais_a[m] for m in MODELOS_CONHECIDOS]
    comp_data_b = [totais_b[m] for m in MODELOS_CONHECIDOS]

    MESES_PT = {
        '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
        '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
        '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
    }

    def fmt_mes(ym):
        partes = ym.split('-')
        return f"{MESES_PT.get(partes[1], partes[1])}/{partes[0]}"

    label_mes_a = fmt_mes(mes_a)
    label_mes_b = fmt_mes(mes_b)

    return render_template(
        'estoque_geral.html',
        painel=painel,
        cores_css=models.CORES_CSS,
        # Comparativo de meses
        mes_a=mes_a, mes_b=mes_b,
        label_mes_a=label_mes_a, label_mes_b=label_mes_b,
        delta_total=delta_total,
        total_a=total_a,
        top2_modelos=top2_modelos,
        comp_labels=comp_labels,
        comp_data_a=comp_data_a,
        comp_data_b=comp_data_b,
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
