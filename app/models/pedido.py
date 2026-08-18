from .connection import get_connection
from .peca import baixar_estoque_por_bom


# ──────────────────────────────────────────────
# CRIAÇÃO DE TABELAS
# ──────────────────────────────────────────────

def criar_tabelas_pedidos():
    """
    Cria pedidos e itens_pedido_scooter.
    CREATE TABLE IF NOT EXISTS — nunca dropa tabela existente.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            num_pedido    TEXT NOT NULL,
            status        TEXT NOT NULL DEFAULT 'RESERVADO',
            data_criacao  TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),
            data_despacho TIMESTAMP DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido_scooter (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id   INTEGER NOT NULL REFERENCES pedidos(id),
            variacao_id INTEGER NOT NULL REFERENCES variacoes(id),
            producao_id INTEGER REFERENCES producao(id),
            quantidade  INTEGER NOT NULL
        )
    """)

    # Migração idempotente (mesmo padrão de custo_unitario em peca.py):
    # adiciona colunas só se ainda não existirem. Preparação p/ C3/C4.
    # prioridade: valores válidos 'BAIXA' | 'MEDIA' | 'ALTA' | 'URGENTE'
    #   (sem CHECK no banco — validação fica na camada de aplicação/UI).
    cols = [r[1] for r in conn.execute("PRAGMA table_info(pedidos)")]
    if 'prioridade' not in cols:
        conn.execute(
            "ALTER TABLE pedidos ADD COLUMN prioridade TEXT DEFAULT 'MEDIA'"
        )
    if 'transportadora' not in cols:
        conn.execute(
            "ALTER TABLE pedidos ADD COLUMN transportadora TEXT DEFAULT NULL"
        )

    conn.commit()
    conn.close()


def atualizar_prioridade_transportadora(pedido_id, prioridade=None,
                                        transportadora=None):
    """
    Atualiza prioridade e/ou transportadora de um pedido.
    Só atualiza os campos que forem passados (não None).
    """
    conn = get_connection()
    if prioridade is not None:
        conn.execute(
            "UPDATE pedidos SET prioridade = ? WHERE id = ?",
            (prioridade, pedido_id)
        )
    if transportadora is not None:
        conn.execute(
            "UPDATE pedidos SET transportadora = ? WHERE id = ?",
            (transportadora, pedido_id)
        )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# AUXILIARES INTERNAS
# ──────────────────────────────────────────────

def _resolver_variacao_id(cursor, modelo_nome, cor_paralama, cor_chassis):
    """
    Resolve o id da variação seguindo EXATAMENTE a mesma lógica
    de registrar_producao() em scooter.py (mesma query condicional
    para TUI POP vs demais modelos). Levanta ValueError se não
    encontrar produto ou variação — mesmas mensagens de erro
    usadas em registrar_producao para consistência.

    Decisão de implementação: registrar_producao filtra por
    edicao_id (vindo do formulário). O fluxo de pedido não tem
    conceito de edição — é sempre a edição padrão. Como todas as
    variações do banco têm edicao_id = 1 (Padrão), fixamos
    `AND edicao_id = 1` para resolver unicamente e evitar
    ambiguidade caso edições adicionais passem a existir.
    """
    produto = cursor.execute(
        "SELECT id FROM produtos WHERE nome = ?", (modelo_nome,)
    ).fetchone()
    if not produto:
        raise ValueError(f"Modelo de produto '{modelo_nome}' não encontrado!")
    produto_id = produto['id']

    if modelo_nome == 'TUI POP':
        variacao = cursor.execute("""
            SELECT id FROM variacoes
            WHERE produto_id = ? AND cor_paralama = ? AND cor_chassis = ? AND edicao_id = 1
        """, (produto_id, cor_paralama, cor_chassis)).fetchone()
    else:
        variacao = cursor.execute("""
            SELECT id FROM variacoes
            WHERE produto_id = ? AND cor_paralama = ? AND edicao_id = 1
        """, (produto_id, cor_paralama)).fetchone()

    if not variacao:
        raise ValueError(f"Variação não encontrada!")

    return variacao['id']


def _tem_bom(cursor, modelo_nome):
    """
    Verifica dinamicamente se existe BOM cadastrada para o
    modelo (query em `bom`, não lista fixa). Retorna bool.
    """
    row = cursor.execute(
        "SELECT 1 FROM bom WHERE modelo = ? LIMIT 1", (modelo_nome,)
    ).fetchone()
    return row is not None


def _itens_do_pedido(conn, pedido_id):
    """Retorna os itens de um pedido com nome_completo (via JOIN variacoes)."""
    itens = conn.execute("""
        SELECT i.id AS item_id, v.nome_completo, i.quantidade
        FROM itens_pedido_scooter i
        JOIN variacoes v ON v.id = i.variacao_id
        WHERE i.pedido_id = ?
        ORDER BY i.id
    """, (pedido_id,)).fetchall()
    return [dict(row) for row in itens]


# ──────────────────────────────────────────────
# CONSULTAS
# ──────────────────────────────────────────────

def buscar_ultimo_num_pedido_usado():
    """
    Retorna o num_pedido do último item de pedido inserido
    (ORDER BY item.id DESC LIMIT 1), independente de status.
    Usado para pré-preencher o modal de produção com o último
    pedido usado (facilita múltiplos registros do mesmo pedido —
    caso de revenda). Retorna '' se nenhum pedido existir ainda.
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT p.num_pedido
        FROM itens_pedido_scooter i
        JOIN pedidos p ON p.id = i.pedido_id
        ORDER BY i.id DESC LIMIT 1
    """).fetchone()
    conn.close()
    return row['num_pedido'] if row else ''


def listar_pedidos_reservados():
    """
    Retorna pedidos com status='RESERVADO', cada um com sua
    lista de itens (JOIN variacoes para trazer nome_completo).
    Formato: lista de dicts
      {'pedido_id':, 'num_pedido':, 'data_criacao':,
       'prioridade':, 'transportadora':,
       'itens': [{'item_id':, 'nome_completo':, 'quantidade':}]}
    Ordenado por data_criacao DESC.
    """
    conn = get_connection()
    pedidos = conn.execute("""
        SELECT id, num_pedido, data_criacao, prioridade, transportadora
        FROM pedidos
        WHERE status = 'RESERVADO'
        ORDER BY data_criacao DESC
    """).fetchall()

    resultado = []
    for p in pedidos:
        resultado.append({
            'pedido_id': p['id'],
            'num_pedido': p['num_pedido'],
            'data_criacao': p['data_criacao'],
            'prioridade': p['prioridade'],
            'transportadora': p['transportadora'],
            'itens': _itens_do_pedido(conn, p['id']),
        })

    conn.close()
    return resultado


def buscar_pedido_por_numero(num_pedido):
    """
    Busca pedido(s) RESERVADO com esse num_pedido exato,
    incluindo itens (mesmo formato de listar_pedidos_reservados).
    Usado na tela de saída para localizar o que despachar.
    Retorna lista vazia se não encontrar.
    """
    conn = get_connection()
    pedidos = conn.execute("""
        SELECT id, num_pedido, data_criacao, prioridade, transportadora
        FROM pedidos
        WHERE num_pedido = ? AND status = 'RESERVADO'
        ORDER BY data_criacao DESC
    """, (num_pedido,)).fetchall()

    resultado = []
    for p in pedidos:
        resultado.append({
            'pedido_id': p['id'],
            'num_pedido': p['num_pedido'],
            'data_criacao': p['data_criacao'],
            'prioridade': p['prioridade'],
            'transportadora': p['transportadora'],
            'itens': _itens_do_pedido(conn, p['id']),
        })

    conn.close()
    return resultado


# ──────────────────────────────────────────────
# CICLO DE VIDA DO PEDIDO
# ──────────────────────────────────────────────

def registrar_producao_pedido(modelo_nome, cor_paralama, cor_chassis,
                               quantidade, num_pedido):
    """
    Registra produção RESERVADA para um pedido:
    1. Resolve variacao_id (mesma lógica de registrar_producao)
    2. INSERT em `producao` (log — aparece em Log de Produção e
       dashboards) SEM incrementar variacoes.estoque_atual
    3. Localiza pedido existente com esse num_pedido e
       status='RESERVADO'; se não existir, cria um novo
    4. INSERT em itens_pedido_scooter (pedido_id, variacao_id,
       producao_id, quantidade)
    5. Se existir BOM para o modelo (via _tem_bom), chama
       baixar_estoque_por_bom(modelo_nome, cor_paralama, quantidade)

    Retorna dict: {'pedido_id':, 'num_pedido':, 'producao_id':,
                   'item_id':}

    Levanta ValueError se modelo/variação não encontrados
    (mesmas mensagens de registrar_producao).
    """
    conn = get_connection()
    cursor = conn.cursor()

    variacao_id = _resolver_variacao_id(cursor, modelo_nome,
                                         cor_paralama, cor_chassis)

    cursor.execute(
        "INSERT INTO producao (variacao_id, quantidade) VALUES (?, ?)",
        (variacao_id, quantidade)
    )
    producao_id = cursor.lastrowid

    # NÃO faz UPDATE em variacoes.estoque_atual — diferença
    # crucial vs registrar_producao() normal. A scooter reservada
    # não conta no estoque geral livre até ser cancelada.

    pedido_row = cursor.execute(
        "SELECT id FROM pedidos WHERE num_pedido = ? AND status = 'RESERVADO'",
        (num_pedido,)
    ).fetchone()

    if pedido_row:
        pedido_id = pedido_row['id']
    else:
        cursor.execute(
            "INSERT INTO pedidos (num_pedido, status) VALUES (?, 'RESERVADO')",
            (num_pedido,)
        )
        pedido_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO itens_pedido_scooter
            (pedido_id, variacao_id, producao_id, quantidade)
        VALUES (?, ?, ?, ?)
    """, (pedido_id, variacao_id, producao_id, quantidade))
    item_id = cursor.lastrowid

    conn.commit()

    if _tem_bom(cursor, modelo_nome):
        baixar_estoque_por_bom(
            modelo=modelo_nome,
            cor_scooter=cor_paralama,
            quantidade_scooters=quantidade
        )

    conn.close()
    return {
        'pedido_id': pedido_id, 'num_pedido': num_pedido,
        'producao_id': producao_id, 'item_id': item_id,
    }


def confirmar_despacho(pedido_id, motivo):
    """
    Confirma o despacho de um pedido reservado:
    1. Busca itens_pedido_scooter do pedido
    2. Para CADA item: INSERT direto em saidas_estoque
       (variacao_id, quantidade, motivo, num_pedido) —
       SEM checar nem descontar variacoes.estoque_atual
       (a reserva nunca entrou no estoque geral)
    3. UPDATE pedidos SET status='DESPACHADO',
       data_despacho=agora WHERE id=pedido_id

    Levanta ValueError se o pedido não existir ou não estiver
    RESERVADO (evita despachar duas vezes).
    """
    conn = get_connection()
    cursor = conn.cursor()

    pedido = cursor.execute(
        "SELECT id, num_pedido, status FROM pedidos WHERE id = ?",
        (pedido_id,)
    ).fetchone()
    if not pedido:
        conn.close()
        raise ValueError(f"Pedido id {pedido_id} não encontrado!")
    if pedido['status'] != 'RESERVADO':
        conn.close()
        raise ValueError(
            f"Pedido '{pedido['num_pedido']}' não está RESERVADO "
            f"(status atual: {pedido['status']}). Não pode ser despachado."
        )

    num_pedido = pedido['num_pedido']

    itens = cursor.execute(
        "SELECT variacao_id, quantidade FROM itens_pedido_scooter WHERE pedido_id = ?",
        (pedido_id,)
    ).fetchall()

    for item in itens:
        cursor.execute("""
            INSERT INTO saidas_estoque (variacao_id, quantidade, motivo, num_pedido)
            VALUES (?, ?, ?, ?)
        """, (item['variacao_id'], item['quantidade'], motivo, num_pedido))

    cursor.execute("""
        UPDATE pedidos
        SET status = 'DESPACHADO',
            data_despacho = strftime('%Y-%m-%d %H:%M:%S','now','localtime')
        WHERE id = ?
    """, (pedido_id,))

    conn.commit()
    conn.close()
    return {
        'pedido_id': pedido_id, 'num_pedido': num_pedido,
        'itens_despachados': len(itens),
    }


def cancelar_pedido(pedido_id):
    """
    Cancela um pedido reservado:
    1. Para CADA item em itens_pedido_scooter: UPDATE variacoes
       SET estoque_atual = estoque_atual + quantidade
       (devolve a scooter já produzida ao estoque geral)
    2. UPDATE pedidos SET status='CANCELADO'
    3. NÃO deleta itens_pedido_scooter nem o registro em
       producao — histórico preservado

    Levanta ValueError se o pedido não existir ou não estiver
    RESERVADO.
    """
    conn = get_connection()
    cursor = conn.cursor()

    pedido = cursor.execute(
        "SELECT id, num_pedido, status FROM pedidos WHERE id = ?",
        (pedido_id,)
    ).fetchone()
    if not pedido:
        conn.close()
        raise ValueError(f"Pedido id {pedido_id} não encontrado!")
    if pedido['status'] != 'RESERVADO':
        conn.close()
        raise ValueError(
            f"Pedido '{pedido['num_pedido']}' não está RESERVADO "
            f"(status atual: {pedido['status']}). Não pode ser cancelado."
        )

    itens = cursor.execute(
        "SELECT variacao_id, quantidade FROM itens_pedido_scooter WHERE pedido_id = ?",
        (pedido_id,)
    ).fetchall()

    for item in itens:
        cursor.execute("""
            UPDATE variacoes
            SET estoque_atual = estoque_atual + ?
            WHERE id = ?
        """, (item['quantidade'], item['variacao_id']))

    cursor.execute(
        "UPDATE pedidos SET status = 'CANCELADO' WHERE id = ?",
        (pedido_id,)
    )

    conn.commit()
    conn.close()
    return {
        'pedido_id': pedido_id, 'num_pedido': pedido['num_pedido'],
        'itens_devolvidos': len(itens),
    }


def editar_item_pedido(item_id, nova_quantidade):
    """
    Ajusta a quantidade de um item de pedido reservado:
    1. Busca item atual (quantidade antiga, producao_id)
    2. Calcula diferença (nova - antiga)
    3. UPDATE itens_pedido_scooter SET quantidade = nova_quantidade
    4. UPDATE producao SET quantidade = nova_quantidade
       WHERE id = producao_id (mantém log sincronizado)

    LIMITAÇÃO DOCUMENTADA (consistente com atualizar_producao
    existente): não reconcilia consumo de peças da BOM
    retroativamente. Se a quantidade mudar significativamente,
    correção manual de estoque de peças pode ser necessária.

    Levanta ValueError se o item não existir ou o pedido não
    estiver mais RESERVADO (não editar após despacho/cancelamento).
    """
    conn = get_connection()
    cursor = conn.cursor()

    item = cursor.execute("""
        SELECT i.id, i.quantidade, i.producao_id, i.pedido_id, p.status, p.num_pedido
        FROM itens_pedido_scooter i
        JOIN pedidos p ON p.id = i.pedido_id
        WHERE i.id = ?
    """, (item_id,)).fetchone()

    if not item:
        conn.close()
        raise ValueError(f"Item de pedido id {item_id} não encontrado!")
    if item['status'] != 'RESERVADO':
        conn.close()
        raise ValueError(
            f"Item do pedido '{item['num_pedido']}' não é editável "
            f"(status atual: {item['status']})."
        )

    # Diferença calculada para referência. A reserva não toca em
    # variacoes.estoque_atual, então não há ajuste de estoque geral
    # aqui; a limitação de reconciliação de peças da BOM está
    # documentada acima.
    _diferenca = nova_quantidade - item['quantidade']

    cursor.execute(
        "UPDATE itens_pedido_scooter SET quantidade = ? WHERE id = ?",
        (nova_quantidade, item_id)
    )

    if item['producao_id'] is not None:
        cursor.execute(
            "UPDATE producao SET quantidade = ? WHERE id = ?",
            (nova_quantidade, item['producao_id'])
        )

    conn.commit()
    conn.close()
    return {
        'item_id': item_id, 'quantidade_antiga': item['quantidade'],
        'quantidade_nova': nova_quantidade, 'diferenca': _diferenca,
    }
