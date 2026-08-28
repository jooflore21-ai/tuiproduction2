import re
from .connection import get_connection

# Cores oficiais para os paralamas TUI
CORES_CSS = {
    "AMARELO": "#f1c40f",
    "CINZA":   "#4d4d4d",
    "AZUL":    "#000099",
    "BRANCO":  "#ecf0f1",
    "BRONZE":  "#a75d25",
    "LARANJA": "#F25C05",
    "PRATA":   "#bdc3c7",
    "PRETO":   "#000000",
    "ROSA":    "#ff79c6",
    "ROXO":    "#592f6a",
    "VERDE":   "#00ff00",
    "VERMELHO":"#d60202",
}

DATA_HORA_FMT = "YYYY-MM-DD HH24:MI:SS"

# ------------------------------
# Criação de tabelas
# ------------------------------
def criar_tabelas():
    """
    CREATE TABLE IF NOT EXISTS em todas — nunca dropa tabela existente.
    Redundante com app/migrate_to_postgres.py (que já cria o schema),
    mas mantido para o app subir sozinho em um Postgres vazio.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            sku TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edicoes (
            id SERIAL PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL
        );
    """)
    cursor.execute(
        "INSERT INTO edicoes (id, nome) VALUES (1, 'Padrão') "
        "ON CONFLICT (id) DO NOTHING"
    )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variacoes (
            id SERIAL PRIMARY KEY,
            produto_id INTEGER NOT NULL REFERENCES produtos(id),
            cor_chassis TEXT,
            cor_paralama TEXT,
            nome_completo TEXT UNIQUE NOT NULL,
            estoque_atual INTEGER NOT NULL DEFAULT 0,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            edicao_id INTEGER REFERENCES edicoes(id) DEFAULT 1
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS producao (
            id SERIAL PRIMARY KEY,
            variacao_id INTEGER NOT NULL REFERENCES variacoes(id),
            quantidade INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assistencia (
            id SERIAL PRIMARY KEY,
            produto_id INTEGER NOT NULL REFERENCES produtos(id),
            quantidade INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saidas_estoque (
            id SERIAL PRIMARY KEY,
            variacao_id INTEGER NOT NULL REFERENCES variacoes(id),
            quantidade INTEGER NOT NULL,
            motivo TEXT NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observacao TEXT,
            num_pedido TEXT DEFAULT ''
        );
    """)

    conn.commit()
    conn.close()


# ------------------------------
# Cadastro inicial de produtos e variações
# ------------------------------
def carregar_variacoes_iniciais():
    conn = get_connection()
    cursor = conn.cursor()

    produtos = [
        ("SKU001", "TUI"),
        ("SKU002", "TUI MAIS"),
        ("SKU003", "TUI POP"),
        ("SKU004", "CAPACETE"),
    ]

    for sku, nome in produtos:
        cursor.execute(
            "INSERT INTO produtos (sku, nome) VALUES (%s, %s) "
            "ON CONFLICT (sku) DO NOTHING",
            (sku, nome)
        )

    conn.commit()

    cursor.execute("SELECT id, nome FROM produtos")
    ids = {row["nome"]: row["id"] for row in cursor.fetchall()}

    cores_paralama = ["AMARELO", "AZUL", "BRANCO", "BRONZE", "CINZA",
                      "LARANJA", "PRATA", "PRETO", "ROSA", "ROXO", "VERDE", "VERMELHO"]

    for cor in cores_paralama:
        cursor.execute(
            "INSERT INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (nome_completo) DO NOTHING",
            (ids["TUI"], None, cor, f"TUI {cor}"))
        cursor.execute(
            "INSERT INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (nome_completo) DO NOTHING",
            (ids["TUI MAIS"], None, cor, f"TUI MAIS {cor}"))

    for cor_chassis in ["PRETO", "BRANCO"]:
        for cor in cores_paralama:
            cursor.execute(
                "INSERT INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT (nome_completo) DO NOTHING",
                (ids["TUI POP"], cor_chassis, cor, f"TUI POP {cor_chassis} {cor}"))

    cursor.execute(
        "INSERT INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) "
        "VALUES (%s, %s, %s, %s) ON CONFLICT (nome_completo) DO NOTHING",
        (ids["CAPACETE"], None, None, "CAPACETE"))

    conn.commit()
    conn.close()


def carregar_variacoes_modelos_novos():
    """
    Semeia produtos + variacoes dos 3 modelos novos de scooter, seguindo
    exatamente o padrão de carregar_variacoes_iniciais(). Idempotente
    (ON CONFLICT DO NOTHING). Estoque inicial 0 (default da coluna estoque_atual).

      - TUI MAIS-S  → variação só por cor de paralama (12), como família MAIS
      - TUI MAIS-LS → variação só por cor de paralama (12), como família MAIS
      - TUI POP-S   → chassis fixo PRETO + cor de paralama (12), como POP

    Os nomes gerados batem com a lógica de nome_completo usada em
    producao.py e saidas.py (MAIS = "MODELO cor"; POP = "MODELO PRETO cor").
    """
    conn = get_connection()
    cursor = conn.cursor()

    produtos = [
        ("SKU005", "TUI MAIS-S"),
        ("SKU006", "TUI POP-S"),
        ("SKU007", "TUI MAIS-LS"),
    ]
    for sku, nome in produtos:
        cursor.execute(
            "INSERT INTO produtos (sku, nome) VALUES (%s, %s) "
            "ON CONFLICT (sku) DO NOTHING",
            (sku, nome))

    conn.commit()

    cursor.execute("SELECT id, nome FROM produtos")
    ids = {row["nome"]: row["id"] for row in cursor.fetchall()}

    cores_paralama = ["AMARELO", "AZUL", "BRANCO", "BRONZE", "CINZA",
                      "LARANJA", "PRATA", "PRETO", "ROSA", "ROXO", "VERDE", "VERMELHO"]

    # Família MAIS: só paralama (cor_chassis NULL)
    for modelo in ("TUI MAIS-S", "TUI MAIS-LS"):
        for cor in cores_paralama:
            cursor.execute(
                "INSERT INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT (nome_completo) DO NOTHING",
                (ids[modelo], None, cor, f"{modelo} {cor}"))

    # Família POP: chassis fixo PRETO + paralama
    for cor in cores_paralama:
        cursor.execute(
            "INSERT INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (nome_completo) DO NOTHING",
            (ids["TUI POP-S"], "PRETO", cor, f"TUI POP-S PRETO {cor}"))

    conn.commit()
    conn.close()


def migrar_motivos_saida():
    """
    Migração idempotente: renomeia motivos antigos de saidas_estoque para
    os novos nomes. Mapeamento autorizado pelo usuário, sem preservar
    correspondência semântica:
      CPF      → CLIENTE
      CNPJ     → REVENDA
      FEIRA    → FEIRA (sem mudança)
      PRESENTE → BONIFICADO
    Rodar múltiplas vezes é seguro: se nenhum registro tiver o motivo
    antigo, o UPDATE simplesmente não afeta nenhuma linha.
    """
    conn = get_connection()
    mapeamento = {
        'CPF': 'CLIENTE',
        'CNPJ': 'REVENDA',
        'PRESENTE': 'BONIFICADO',
    }
    for antigo, novo in mapeamento.items():
        conn.execute(
            "UPDATE saidas_estoque SET motivo = %s WHERE motivo = %s",
            (novo, antigo)
        )
    conn.commit()
    conn.close()


# ------------------------------
# Edições
# ------------------------------
def criar_edicao(nome):
    """Insere uma nova edição/cliente e retorna o id gerado."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edicoes (nome) VALUES (%s) RETURNING id", (nome,))
    novo_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()
    return novo_id


def listar_edicoes():
    """Retorna todas as edições ordenadas por nome."""
    conn = get_connection()
    edicoes = conn.execute("SELECT id, nome FROM edicoes ORDER BY nome").fetchall()
    conn.close()
    return edicoes


# ------------------------------
# Produção
# ------------------------------
def registrar_producao(modelo_nome, cor_paralama, cor_chassis, edicao_id, quantidade):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM produtos WHERE nome = %s", (modelo_nome,))
    produto = cursor.fetchone()

    if not produto:
        raise ValueError(f"Modelo de produto '{modelo_nome}' não encontrado!")
    produto_id = produto['id']

    if modelo_nome == 'TUI POP':
        cursor.execute("""
            SELECT id FROM variacoes
            WHERE produto_id = %s AND cor_paralama = %s AND cor_chassis = %s AND edicao_id = %s
        """, (produto_id, cor_paralama, cor_chassis, edicao_id))
    else:
        cursor.execute("""
            SELECT id FROM variacoes
            WHERE produto_id = %s AND cor_paralama = %s AND edicao_id = %s
        """, (produto_id, cor_paralama, edicao_id))

    variacao = cursor.fetchone()

    if not variacao:
        raise ValueError(f"Variação não encontrada!")

    variacao_id = variacao["id"]

    cursor.execute("INSERT INTO producao (variacao_id, quantidade) VALUES (%s, %s)", (variacao_id, quantidade))

    cursor.execute("""
        UPDATE variacoes
        SET estoque_atual = estoque_atual + %s,
            data_atualizacao = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (quantidade, variacao_id))

    # Reservado: lógica de capacete será implementada em versão futura.

    conn.commit()
    conn.close()


def consultar_producao(periodo="diario"):
    conn = get_connection()
    cursor = conn.cursor()

    base_query = f"""
        SELECT p.id, v.nome_completo, p.quantidade,
               to_char(p.data_hora, '{DATA_HORA_FMT}') AS data_hora
        FROM producao p
        JOIN variacoes v ON v.id = p.variacao_id
    """

    params = ()
    if re.match(r'^\d{4}-\d{2}$', periodo):
        query = f"{base_query} WHERE to_char(p.data_hora, 'YYYY-MM') = %s ORDER BY p.data_hora DESC"
        params = (periodo,)
    elif periodo == "diario":
        query = f"{base_query} WHERE p.data_hora::date = CURRENT_DATE ORDER BY p.data_hora DESC"
    elif periodo == "semanal":
        query = f"{base_query} WHERE p.data_hora::date >= CURRENT_DATE - INTERVAL '7 days' ORDER BY p.data_hora DESC"
    elif periodo == "mensal":
        query = f"{base_query} WHERE to_char(p.data_hora, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM') ORDER BY p.data_hora DESC"
    else:
        query = f"{base_query} WHERE p.data_hora::date = CURRENT_DATE ORDER BY p.data_hora DESC"

    producoes = cursor.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in producoes]


# ------------------------------
# Assistência
# ------------------------------
def registrar_assistencia(nome_produto, quantidade):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM produtos WHERE nome = %s", (nome_produto,))
    produto = cursor.fetchone()
    if not produto:
        conn.close()
        raise ValueError(f"Produto '{nome_produto}' não encontrado!")

    produto_id = produto["id"]
    cursor.execute("INSERT INTO assistencia (produto_id, quantidade) VALUES (%s, %s)", (produto_id, quantidade))

    conn.commit()
    conn.close()


def consultar_assistencia(periodo="diario"):
    conn = get_connection()
    cursor = conn.cursor()

    base_query = f"""
        SELECT a.id, p.nome, a.quantidade,
               to_char(a.data_hora, '{DATA_HORA_FMT}') AS data_hora
        FROM assistencia a
        JOIN produtos p ON p.id = a.produto_id
    """

    params = ()
    if re.match(r'^\d{4}-\d{2}$', periodo):
        query = f"{base_query} WHERE to_char(a.data_hora, 'YYYY-MM') = %s ORDER BY a.data_hora DESC"
        params = (periodo,)
    elif periodo == "diario":
        query = f"{base_query} WHERE a.data_hora::date = CURRENT_DATE ORDER BY a.data_hora DESC"
    elif periodo == "semanal":
        query = f"{base_query} WHERE a.data_hora::date >= CURRENT_DATE - INTERVAL '6 days' ORDER BY a.data_hora DESC"
    elif periodo == "mensal":
        query = f"{base_query} WHERE to_char(a.data_hora, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM') ORDER BY a.data_hora DESC"
    else:
        query = f"{base_query} WHERE a.data_hora::date = CURRENT_DATE ORDER BY a.data_hora DESC"

    embalagens = cursor.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in embalagens]


def deletar_producao(id_producao):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT variacao_id, quantidade FROM producao WHERE id = %s", (id_producao,))
    registro = cursor.fetchone()
    if not registro:
        raise ValueError("Registro de produção não encontrado!")

    cursor.execute("UPDATE variacoes SET estoque_atual = estoque_atual - %s WHERE id = %s",
                   (registro['quantidade'], registro['variacao_id']))
    cursor.execute("DELETE FROM producao WHERE id = %s", (id_producao,))

    conn.commit()
    conn.close()


def deletar_assistencia(id_assistencia):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM assistencia WHERE id = %s", (id_assistencia,))
    conn.commit()
    conn.close()


def buscar_producao_por_id(id_producao):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, variacao_id, quantidade FROM producao WHERE id = %s", (id_producao,))
    registro = cursor.fetchone()
    conn.close()
    return dict(registro) if registro else None


def atualizar_producao(id_producao, nova_quantidade, nova_data=None):
    conn = get_connection()
    cursor = conn.cursor()

    registro_antigo = buscar_producao_por_id(id_producao)
    if not registro_antigo:
        raise ValueError("Registro de produção não encontrado!")

    quantidade_antiga = registro_antigo['quantidade']
    diferenca_estoque = nova_quantidade - quantidade_antiga

    cursor.execute("UPDATE variacoes SET estoque_atual = estoque_atual + %s WHERE id = %s",
                   (diferenca_estoque, registro_antigo['variacao_id']))

    if nova_data:
        data_formatada = nova_data.replace('T', ' ')
        if len(data_formatada) == 16:
            data_formatada += ":00"
        cursor.execute("UPDATE producao SET quantidade = %s, data_hora = %s WHERE id = %s",
                       (nova_quantidade, data_formatada, id_producao))
    else:
        cursor.execute("UPDATE producao SET quantidade = %s WHERE id = %s",
                       (nova_quantidade, id_producao))

    conn.commit()
    conn.close()


def atualizar_assistencia(id_assistencia, nova_quantidade):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE assistencia SET quantidade = %s WHERE id = %s",
                   (nova_quantidade, id_assistencia))
    conn.commit()
    conn.close()


# ------------------------------
# Estoque
# ------------------------------
def consultar_estoque():
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        SELECT v.nome_completo, v.estoque_atual,
               to_char(v.data_atualizacao, '{DATA_HORA_FMT}') AS data_atualizacao,
               v.edicao_id, COALESCE(e.nome, 'Padrão') as edicao_nome
        FROM variacoes v
        LEFT JOIN edicoes e ON e.id = v.edicao_id
        WHERE v.estoque_atual > 0
        ORDER BY v.nome_completo
    """
    estoque = cursor.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in estoque]


def consultar_estoque_por_modelo():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            p.nome,
            SUM(v.estoque_atual) as estoque_total
        FROM variacoes v
        JOIN produtos p ON v.produto_id = p.id
        GROUP BY p.nome
        ORDER BY p.nome;
    """
    estoque_agrupado = cursor.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in estoque_agrupado]


# ------------------------------
# Saída
# ------------------------------
def registrar_saida(nome_completo, quantidade, motivo, num_pedido='', observacao=''):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, estoque_atual FROM variacoes WHERE nome_completo = %s", (nome_completo,))
    variacao = cursor.fetchone()

    if not variacao:
        raise ValueError(f"Produto '{nome_completo}' não encontrado!")

    if variacao['estoque_atual'] < quantidade:
        raise ValueError(
            f"Estoque insuficiente para '{nome_completo}'. "
            f"Em estoque: {variacao['estoque_atual']}, Saída solicitada: {quantidade}"
        )

    novo_estoque = variacao['estoque_atual'] - quantidade
    cursor.execute(
        "UPDATE variacoes SET estoque_atual = %s, "
        "data_atualizacao = CURRENT_TIMESTAMP WHERE id = %s",
        (novo_estoque, variacao['id'])
    )

    cursor.execute(
        "INSERT INTO saidas_estoque (variacao_id, quantidade, motivo, num_pedido, observacao) "
        "VALUES (%s, %s, %s, %s, %s)",
        (variacao['id'], quantidade, motivo, num_pedido, observacao)
    )

    conn.commit()
    conn.close()


def consultar_saidas(periodo="diario", data_inicio=None, data_fim=None):
    conn = get_connection()
    cursor = conn.cursor()

    base_query = f"""
        SELECT s.id, v.nome_completo, s.quantidade, s.motivo,
               to_char(s.data_hora, '{DATA_HORA_FMT}') AS data_hora,
               COALESCE(s.num_pedido, '') as num_pedido
        FROM saidas_estoque s
        JOIN variacoes v ON v.id = s.variacao_id
    """

    if data_inicio and data_fim:
        query = f"{base_query} WHERE s.data_hora::date BETWEEN %s AND %s ORDER BY s.data_hora DESC"
        params = (data_inicio, data_fim)
    elif data_inicio:
        query = f"{base_query} WHERE s.data_hora::date >= %s ORDER BY s.data_hora DESC"
        params = (data_inicio,)
    elif data_fim:
        query = f"{base_query} WHERE s.data_hora::date <= %s ORDER BY s.data_hora DESC"
        params = (data_fim,)
    elif periodo == "diario":
        query = f"{base_query} WHERE s.data_hora::date = CURRENT_DATE ORDER BY s.data_hora DESC"
        params = ()
    elif periodo == "semanal":
        query = f"{base_query} WHERE s.data_hora::date >= CURRENT_DATE - INTERVAL '6 days' ORDER BY s.data_hora DESC"
        params = ()
    elif periodo == "mensal":
        query = f"{base_query} WHERE to_char(s.data_hora, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM') ORDER BY s.data_hora DESC"
        params = ()
    elif periodo == "ultimos_30_dias":
        query = f"{base_query} WHERE s.data_hora::date >= CURRENT_DATE - INTERVAL '29 days' ORDER BY s.data_hora DESC"
        params = ()
    else:
        query = f"{base_query} WHERE s.data_hora::date = CURRENT_DATE ORDER BY s.data_hora DESC"
        params = ()

    saidas = cursor.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in saidas]


def deletar_saida(id_saida):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT variacao_id, quantidade FROM saidas_estoque WHERE id = %s", (id_saida,))
    registro = cursor.fetchone()
    if not registro:
        raise ValueError("Registro de saída não encontrado!")

    cursor.execute("UPDATE variacoes SET estoque_atual = estoque_atual + %s WHERE id = %s",
                   (registro['quantidade'], registro['variacao_id']))
    cursor.execute("DELETE FROM saidas_estoque WHERE id = %s", (id_saida,))

    conn.commit()
    conn.close()


def atualizar_saida(id_saida, nova_quantidade):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT variacao_id, quantidade FROM saidas_estoque WHERE id = %s", (id_saida,))
    registro_antigo = cursor.fetchone()
    if not registro_antigo:
        raise ValueError("Registro de saída não encontrado!")

    quantidade_antiga = registro_antigo['quantidade']
    variacao_id = registro_antigo['variacao_id']

    cursor.execute("SELECT estoque_atual FROM variacoes WHERE id = %s", (variacao_id,))
    estoque_atual = cursor.fetchone()['estoque_atual']

    if (estoque_atual + quantidade_antiga) < nova_quantidade:
        raise ValueError(
            f"Estoque insuficiente para a alteração. "
            f"Disponível: {estoque_atual + quantidade_antiga}, Solicitado: {nova_quantidade}"
        )

    diferenca_estoque = nova_quantidade - quantidade_antiga
    cursor.execute("UPDATE variacoes SET estoque_atual = estoque_atual - %s WHERE id = %s",
                   (diferenca_estoque, variacao_id))
    cursor.execute("UPDATE saidas_estoque SET quantidade = %s WHERE id = %s",
                   (nova_quantidade, id_saida))

    conn.commit()
    conn.close()
