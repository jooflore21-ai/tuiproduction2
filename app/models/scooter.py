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

# ------------------------------
# Criação de tabelas
# ------------------------------
def criar_tabelas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            cor_chassis TEXT,
            cor_paralama TEXT,
            nome_completo TEXT UNIQUE NOT NULL,
            estoque_atual INTEGER NOT NULL DEFAULT 0,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS producao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variacao_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
            FOREIGN KEY (variacao_id) REFERENCES variacoes (id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assistencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saidas_estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variacao_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            motivo TEXT NOT NULL, -- CPF, CNPJ, FEIRA, PRESENTE
            data_hora TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
            observacao TEXT,
            FOREIGN KEY (variacao_id) REFERENCES variacoes (id)
        );
    """)

    try:
        cursor.execute("ALTER TABLE saidas_estoque ADD COLUMN num_pedido TEXT DEFAULT ''")
    except Exception:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edicoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        );
    """)

    cursor.execute("INSERT OR IGNORE INTO edicoes (id, nome) VALUES (1, 'Padrão')")

    try:
        cursor.execute("ALTER TABLE variacoes ADD COLUMN edicao_id INTEGER REFERENCES edicoes(id) DEFAULT 1")
    except Exception:
        pass

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
        cursor.execute("INSERT OR IGNORE INTO produtos (sku, nome) VALUES (?, ?)", (sku, nome))

    conn.commit()

    cursor.execute("SELECT id, nome FROM produtos")
    ids = {row["nome"]: row["id"] for row in cursor.fetchall()}

    cores_paralama = ["AMARELO", "AZUL", "BRANCO", "BRONZE", "CINZA",
                      "LARANJA", "PRATA", "PRETO", "ROSA", "ROXO", "VERDE", "VERMELHO"]

    for cor in cores_paralama:
        cursor.execute("INSERT OR IGNORE INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) VALUES (?, ?, ?, ?)",
                       (ids["TUI"], None, cor, f"TUI {cor}"))
        cursor.execute("INSERT OR IGNORE INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) VALUES (?, ?, ?, ?)",
                       (ids["TUI MAIS"], None, cor, f"TUI MAIS {cor}"))

    for cor_chassis in ["PRETO", "BRANCO"]:
        for cor in cores_paralama:
            cursor.execute("INSERT OR IGNORE INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) VALUES (?, ?, ?, ?)",
                           (ids["TUI POP"], cor_chassis, cor, f"TUI POP {cor_chassis} {cor}"))

    cursor.execute("INSERT OR IGNORE INTO variacoes (produto_id, cor_chassis, cor_paralama, nome_completo) VALUES (?, ?, ?, ?)",
                   (ids["CAPACETE"], None, None, "CAPACETE"))

    conn.commit()
    conn.close()


# ------------------------------
# Edições
# ------------------------------
def criar_edicao(nome):
    """Insere uma nova edição/cliente e retorna o id gerado."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edicoes (nome) VALUES (?)", (nome,))
    conn.commit()
    novo_id = cursor.lastrowid
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

    cursor.execute("SELECT id FROM produtos WHERE nome = ?", (modelo_nome,))
    produto = cursor.fetchone()

    if not produto:
        raise ValueError(f"Modelo de produto '{modelo_nome}' não encontrado!")
    produto_id = produto['id']

    if modelo_nome == 'TUI POP':
        cursor.execute("""
            SELECT id FROM variacoes
            WHERE produto_id = ? AND cor_paralama = ? AND cor_chassis = ? AND edicao_id = ?
        """, (produto_id, cor_paralama, cor_chassis, edicao_id))
    else:
        cursor.execute("""
            SELECT id FROM variacoes
            WHERE produto_id = ? AND cor_paralama = ? AND edicao_id = ?
        """, (produto_id, cor_paralama, edicao_id))

    variacao = cursor.fetchone()

    if not variacao:
        raise ValueError(f"Variação não encontrada!")

    variacao_id = variacao["id"]

    cursor.execute("INSERT INTO producao (variacao_id, quantidade) VALUES (?, ?)", (variacao_id, quantidade))

    cursor.execute("""
        UPDATE variacoes
        SET estoque_atual = estoque_atual + ?,
            data_atualizacao = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
        WHERE id = ?
    """, (quantidade, variacao_id))

    # Reservado: lógica de capacete será implementada em versão futura.

    conn.commit()
    conn.close()


def consultar_producao(periodo="diario"):
    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT p.id, v.nome_completo, p.quantidade, p.data_hora
        FROM producao p
        JOIN variacoes v ON v.id = p.variacao_id
    """

    if re.match(r'^\d{4}-\d{2}$', periodo):
        query = f"""
            {base_query}
            WHERE strftime('%Y-%m', p.data_hora) = '{periodo}'
            ORDER BY p.data_hora DESC
        """
    elif periodo == "diario":
        query = f"{base_query} WHERE date(p.data_hora) = date('now', 'localtime') ORDER BY p.data_hora DESC"
    elif periodo == "semanal":
        query = f"{base_query} WHERE date(p.data_hora) >= date('now', '-7 days', 'localtime') ORDER BY p.data_hora DESC"
    elif periodo == "mensal":
        query = f"{base_query} WHERE strftime('%Y-%m', p.data_hora) = strftime('%Y-%m', 'now', 'localtime') ORDER BY p.data_hora DESC"
    else:
        query = f"{base_query} WHERE date(p.data_hora) = date('now', 'localtime') ORDER BY p.data_hora DESC"

    producoes = cursor.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in producoes]


# ------------------------------
# Assistência
# ------------------------------
def registrar_assistencia(nome_produto, quantidade):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM produtos WHERE nome = ?", (nome_produto,))
    produto = cursor.fetchone()
    if not produto:
        conn.close()
        raise ValueError(f"Produto '{nome_produto}' não encontrado!")

    produto_id = produto["id"]
    cursor.execute("INSERT INTO assistencia (produto_id, quantidade) VALUES (?, ?)", (produto_id, quantidade))

    conn.commit()
    conn.close()


def consultar_assistencia(periodo="diario"):
    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT a.id, p.nome, a.quantidade, a.data_hora
        FROM assistencia a
        JOIN produtos p ON p.id = a.produto_id
    """

    if re.match(r'^\d{4}-\d{2}$', periodo):
        query = f"{base_query} WHERE strftime('%Y-%m', a.data_hora) = '{periodo}' ORDER BY a.data_hora DESC"
    elif periodo == "diario":
        query = f"{base_query} WHERE date(a.data_hora) = date('now', 'localtime') ORDER BY a.data_hora DESC"
    elif periodo == "semanal":
        query = f"{base_query} WHERE date(a.data_hora) >= date('now', '-6 days', 'localtime') ORDER BY a.data_hora DESC"
    elif periodo == "mensal":
        query = f"{base_query} WHERE strftime('%Y-%m', a.data_hora) = strftime('%Y-%m', 'now', 'localtime') ORDER BY a.data_hora DESC"
    else:
        query = f"{base_query} WHERE date(a.data_hora) = date('now', 'localtime') ORDER BY a.data_hora DESC"

    embalagens = cursor.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in embalagens]


def deletar_producao(id_producao):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT variacao_id, quantidade FROM producao WHERE id = ?", (id_producao,))
    registro = cursor.fetchone()
    if not registro:
        raise ValueError("Registro de produção não encontrado!")

    cursor.execute("UPDATE variacoes SET estoque_atual = estoque_atual - ? WHERE id = ?",
                   (registro['quantidade'], registro['variacao_id']))
    cursor.execute("DELETE FROM producao WHERE id = ?", (id_producao,))

    conn.commit()
    conn.close()


def deletar_assistencia(id_assistencia):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM assistencia WHERE id = ?", (id_assistencia,))
    conn.commit()
    conn.close()


def buscar_producao_por_id(id_producao):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, variacao_id, quantidade FROM producao WHERE id = ?", (id_producao,))
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

    cursor.execute("UPDATE variacoes SET estoque_atual = estoque_atual + ? WHERE id = ?",
                   (diferenca_estoque, registro_antigo['variacao_id']))

    if nova_data:
        data_formatada = nova_data.replace('T', ' ')
        if len(data_formatada) == 16:
            data_formatada += ":00"
        cursor.execute("UPDATE producao SET quantidade = ?, data_hora = ? WHERE id = ?",
                       (nova_quantidade, data_formatada, id_producao))
    else:
        cursor.execute("UPDATE producao SET quantidade = ? WHERE id = ?",
                       (nova_quantidade, id_producao))

    conn.commit()
    conn.close()


def atualizar_assistencia(id_assistencia, nova_quantidade):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE assistencia SET quantidade = ? WHERE id = ?",
                   (nova_quantidade, id_assistencia))
    conn.commit()
    conn.close()


# ------------------------------
# Estoque
# ------------------------------
def consultar_estoque():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT v.nome_completo, v.estoque_atual, v.data_atualizacao,
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

    cursor.execute("SELECT id, estoque_atual FROM variacoes WHERE nome_completo = ?", (nome_completo,))
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
        "UPDATE variacoes SET estoque_atual = ?, "
        "data_atualizacao = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime') WHERE id = ?",
        (novo_estoque, variacao['id'])
    )

    cursor.execute(
        "INSERT INTO saidas_estoque (variacao_id, quantidade, motivo, num_pedido, observacao) "
        "VALUES (?, ?, ?, ?, ?)",
        (variacao['id'], quantidade, motivo, num_pedido, observacao)
    )

    conn.commit()
    conn.close()


def consultar_saidas(periodo="diario", data_inicio=None, data_fim=None):
    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT s.id, v.nome_completo, s.quantidade, s.motivo, s.data_hora,
               COALESCE(s.num_pedido, '') as num_pedido
        FROM saidas_estoque s
        JOIN variacoes v ON v.id = s.variacao_id
    """

    if data_inicio and data_fim:
        query = f"{base_query} WHERE date(s.data_hora) BETWEEN '{data_inicio}' AND '{data_fim}' ORDER BY s.data_hora DESC"
    elif data_inicio:
        query = f"{base_query} WHERE date(s.data_hora) >= '{data_inicio}' ORDER BY s.data_hora DESC"
    elif data_fim:
        query = f"{base_query} WHERE date(s.data_hora) <= '{data_fim}' ORDER BY s.data_hora DESC"
    elif periodo == "diario":
        query = f"{base_query} WHERE date(s.data_hora) = date('now', 'localtime') ORDER BY s.data_hora DESC"
    elif periodo == "semanal":
        query = f"{base_query} WHERE date(s.data_hora) >= date('now', '-6 days', 'localtime') ORDER BY s.data_hora DESC"
    elif periodo == "mensal":
        query = f"{base_query} WHERE strftime('%Y-%m', s.data_hora) = strftime('%Y-%m', 'now', 'localtime') ORDER BY s.data_hora DESC"
    elif periodo == "ultimos_30_dias":
        query = f"{base_query} WHERE date(s.data_hora) >= date('now', '-29 days', 'localtime') ORDER BY s.data_hora DESC"
    else:
        query = f"{base_query} WHERE date(s.data_hora) = date('now', 'localtime') ORDER BY s.data_hora DESC"

    saidas = cursor.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in saidas]


def deletar_saida(id_saida):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT variacao_id, quantidade FROM saidas_estoque WHERE id = ?", (id_saida,))
    registro = cursor.fetchone()
    if not registro:
        raise ValueError("Registro de saída não encontrado!")

    cursor.execute("UPDATE variacoes SET estoque_atual = estoque_atual + ? WHERE id = ?",
                   (registro['quantidade'], registro['variacao_id']))
    cursor.execute("DELETE FROM saidas_estoque WHERE id = ?", (id_saida,))

    conn.commit()
    conn.close()


def atualizar_saida(id_saida, nova_quantidade):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT variacao_id, quantidade FROM saidas_estoque WHERE id = ?", (id_saida,))
    registro_antigo = cursor.fetchone()
    if not registro_antigo:
        raise ValueError("Registro de saída não encontrado!")

    quantidade_antiga = registro_antigo['quantidade']
    variacao_id = registro_antigo['variacao_id']

    cursor.execute("SELECT estoque_atual FROM variacoes WHERE id = ?", (variacao_id,))
    estoque_atual = cursor.fetchone()['estoque_atual']

    if (estoque_atual + quantidade_antiga) < nova_quantidade:
        raise ValueError(
            f"Estoque insuficiente para a alteração. "
            f"Disponível: {estoque_atual + quantidade_antiga}, Solicitado: {nova_quantidade}"
        )

    diferenca_estoque = nova_quantidade - quantidade_antiga
    cursor.execute("UPDATE variacoes SET estoque_atual = estoque_atual - ? WHERE id = ?",
                   (diferenca_estoque, variacao_id))
    cursor.execute("UPDATE saidas_estoque SET quantidade = ? WHERE id = ?",
                   (nova_quantidade, id_saida))

    conn.commit()
    conn.close()
