import calendar
from datetime import date, timedelta

from .connection import get_connection

MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
}


# ──────────────────────────────────────────────
# CONFIGURAÇÃO DE METAS
# ──────────────────────────────────────────────

def obter_metas_config():
    """Lista os setores com a meta_diaria configurada, ordenados por metas_setores.ordem."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.id, s.nome, s.ordem, COALESCE(c.meta_diaria, 0) AS meta_diaria
        FROM metas_setores s
        LEFT JOIN metas_config c ON c.setor = s.id
        ORDER BY s.ordem
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def atualizar_meta_diaria(setor, meta_diaria):
    conn = get_connection()
    conn.execute(
        "UPDATE metas_config SET meta_diaria = %s, updated_at = CURRENT_TIMESTAMP WHERE setor = %s",
        (meta_diaria, setor)
    )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# DIAS ÚTEIS (seg–sex, sem feriados)
# ──────────────────────────────────────────────

def calcular_dias_uteis_mes(ano, mes):
    """Conta dias úteis (segunda a sexta) do mês inteiro. Não desconta feriados."""
    total_dias = calendar.monthrange(ano, mes)[1]
    return sum(
        1 for dia in range(1, total_dias + 1)
        if date(ano, mes, dia).weekday() < 5
    )


def calcular_dias_uteis_semana_atual(ano, mes, dia):
    """
    Conta dias úteis (segunda a sexta) da semana corrente que contém a
    data informada. Se a semana cruzar a virada de mês, conta só os dias
    úteis que caem dentro do mês informado — a meta semanal representa
    a fração da semana pertencente a este mês.
    """
    referencia = date(ano, mes, dia)
    segunda = referencia - timedelta(days=referencia.weekday())
    dias_uteis = 0
    for i in range(5):
        d = segunda + timedelta(days=i)
        if d.year == ano and d.month == mes:
            dias_uteis += 1
    return dias_uteis


# ──────────────────────────────────────────────
# PRODUÇÃO REAL — EMBALAGEM (tabela producao)
# ──────────────────────────────────────────────

def obter_producao_embalagem_hoje():
    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(SUM(quantidade), 0) AS total
        FROM producao
        WHERE data_hora::date = CURRENT_DATE
    """).fetchone()
    conn.close()
    return row['total']


def obter_producao_embalagem_semana():
    """Soma da semana corrente (segunda até hoje)."""
    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(SUM(quantidade), 0) AS total
        FROM producao
        WHERE data_hora >= date_trunc('week', CURRENT_DATE)
    """).fetchone()
    conn.close()
    return row['total']


def obter_producao_embalagem_mes():
    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(SUM(quantidade), 0) AS total
        FROM producao
        WHERE to_char(data_hora, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM')
    """).fetchone()
    conn.close()
    return row['total']


# ──────────────────────────────────────────────
# PAINEL
# ──────────────────────────────────────────────

def _bloco_meta(meta, produzido):
    faltam = meta - produzido
    percentual = int(round((produzido / meta) * 100)) if meta > 0 else 0
    return {'meta': meta, 'produzido': produzido, 'faltam': faltam, 'percentual': percentual}


def montar_dados_painel():
    hoje = date.today()
    ano, mes, dia = hoje.year, hoje.month, hoje.day

    dias_uteis_mes = calcular_dias_uteis_mes(ano, mes)
    dias_uteis_semana = calcular_dias_uteis_semana_atual(ano, mes, dia)

    produzido_hoje = obter_producao_embalagem_hoje()
    produzido_semana = obter_producao_embalagem_semana()
    produzido_mes = obter_producao_embalagem_mes()

    metas_config = obter_metas_config()
    meta_embalagem = next(
        (m['meta_diaria'] for m in metas_config if m['id'] == 'embalagem'), 0
    )

    # Meta geral = meta do setor Embalagem (produto final da fábrica).
    geral = {
        'diaria':  _bloco_meta(meta_embalagem, produzido_hoje),
        'semanal': _bloco_meta(meta_embalagem * dias_uteis_semana, produzido_semana),
        'mensal':  _bloco_meta(meta_embalagem * dias_uteis_mes, produzido_mes),
    }

    # Outros setores ficam zerados até o MES ser ativado — só Embalagem
    # tem dado real hoje (log de producao).
    setores = []
    for s in metas_config:
        produzido = produzido_hoje if s['id'] == 'embalagem' else 0
        bloco = _bloco_meta(s['meta_diaria'], produzido)
        setores.append({
            'id': s['id'],
            'nome': s['nome'],
            'meta_diaria': s['meta_diaria'],
            'produzido_hoje': produzido,
            'faltam': bloco['faltam'],
            'percentual': bloco['percentual'],
        })

    return {
        'data_hora_atual': hoje.strftime('%d/%m/%Y'),
        'mes_ano': f"{MESES_PT[mes]} de {ano}",
        'dias_uteis_mes': dias_uteis_mes,
        'dias_uteis_semana': dias_uteis_semana,
        'geral': geral,
        'setores': setores,
    }
