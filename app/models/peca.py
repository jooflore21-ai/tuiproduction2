from .connection import get_connection

CORES_PARALAMA = [
    'AMARELO', 'AZUL', 'BRANCO', 'BRONZE', 'CINZA',
    'LARANJA', 'PRATA', 'PRETO', 'ROSA', 'ROXO', 'VERDE', 'VERMELHO',
]

DATA_HORA_FMT = "YYYY-MM-DD HH24:MI:SS"


# ──────────────────────────────────────────────
# CRIAÇÃO DE TABELAS
# ──────────────────────────────────────────────

def criar_tabelas_pecas():
    """
    Cria as 4 tabelas do módulo de peças.
    CREATE TABLE IF NOT EXISTS em todas — nunca dropa tabela existente.
    Redundante com app/migrate_to_postgres.py, mantido para o app
    subir sozinho em um Postgres vazio.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pecas (
            id               SERIAL PRIMARY KEY,
            codigo           TEXT UNIQUE NOT NULL,
            nome             TEXT NOT NULL,
            origem           TEXT NOT NULL,
            container_tipo   TEXT DEFAULT 'PADRAO',
            tem_variacao_cor INTEGER DEFAULT 0,
            peca_pai_id      INTEGER REFERENCES pecas(id),
            ativo            INTEGER DEFAULT 1,
            custo_unitario   REAL DEFAULT 0
        )
    """)
    cursor.execute(
        "ALTER TABLE pecas ADD COLUMN IF NOT EXISTS custo_unitario REAL DEFAULT 0"
    )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estoque_pecas (
            id          SERIAL PRIMARY KEY,
            peca_id     INTEGER NOT NULL REFERENCES pecas(id),
            cor         TEXT DEFAULT NULL,
            quantidade  INTEGER NOT NULL DEFAULT 0,
            UNIQUE(peca_id, cor)
        )
    """)

    # Índice parcial para garantir idempotência do seed quando cor IS NULL.
    # UNIQUE(peca_id, cor) não impede duas linhas com cor=NULL, pois
    # NULL != NULL na verificação de unicidade (mesma semântica no Postgres).
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_ep_peca_null_cor
        ON estoque_pecas(peca_id) WHERE cor IS NULL
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes_peca (
            id             SERIAL PRIMARY KEY,
            peca_id        INTEGER NOT NULL REFERENCES pecas(id),
            cor            TEXT DEFAULT NULL,
            tipo           TEXT NOT NULL,
            quantidade     INTEGER NOT NULL,
            motivo_detalhe TEXT DEFAULT '',
            num_pedido     TEXT DEFAULT '',
            num_lote       TEXT DEFAULT '',
            modelo_scooter TEXT DEFAULT NULL,
            data_hora      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bom (
            id              SERIAL PRIMARY KEY,
            modelo          TEXT NOT NULL,
            peca_id         INTEGER NOT NULL REFERENCES pecas(id),
            usa_cor_scooter INTEGER DEFAULT 0,
            cor_fixa        TEXT DEFAULT NULL,
            quantidade      INTEGER NOT NULL DEFAULT 1,
            UNIQUE(modelo, peca_id)
        )
    """)

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# SEED — CARGA INICIAL DE PEÇAS
# ──────────────────────────────────────────────

def carregar_pecas_iniciais():
    """
    Insere todas as peças de forma idempotente (ON CONFLICT DO NOTHING).
    Inicializa estoque_pecas com quantidade 0.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── Peças raiz ──────────────────────────────────────────────────────────
    pecas_raiz = [
        # (codigo, nome, origem, container_tipo, tem_variacao_cor)
        ('RD-TRAS',    'Roda traseira completa',          'IMPORTADA',    'PADRAO',  0),
        ('PEDAL-FD',   'Pedal ferro retrátil direito',    'FERRAMENTARIA','PADRAO',  0),
        ('PEDAL-FE',   'Pedal ferro retrátil esquerdo',   'FERRAMENTARIA','PADRAO',  0),
        ('PARALAMA',   'Kit par paralama',                'IMPORTADA',    'PADRAO',  1),
        ('QUADRO-MAIS','Quadro TUI MAIS',                 'FERRAMENTARIA','PADRAO',  0),
        ('QUADRO-POP', 'Quadro TUI POP',                  'FERRAMENTARIA','PADRAO',  0),
        ('FREIO-TRAS', 'Kit freio traseiro',              'IMPORTADA',    'PADRAO',  0),
        ('FREIO-DI',   'Kit freio dianteiro',             'IMPORTADA',    'PADRAO',  0),
        ('ENC-MAIS',   'Suporte encosto TUI MAIS',        'FERRAMENTARIA','PADRAO',  0),
        ('ENC-POP',    'Suporte encosto TUI POP',         'FERRAMENTARIA','PADRAO',  0),
        ('RD-DI',      'Roda dianteira completa',         'IMPORTADA',    'PADRAO',  0),
        ('PEZINHO',    'Pezinho de descanso',             'FERRAMENTARIA','PADRAO',  0),
        ('MOLA-PEZ',   'Mola do pezinho',                 'IMPORTADA',    'PADRAO',  0),
        ('PAINEL-LCD', 'Painel LCD',                      'IMPORTADA',    'PADRAO',  0),
        ('RETROVISOR', 'Kit retrovisor',                  'IMPORTADA',    'PADRAO',  0),
        ('MESA-GUIDA', 'Mesa suporte guidão',             'IMPORTADA',    'PADRAO',  0),
        ('MANOPLA',    'Manopla esquerda',                'IMPORTADA',    'PADRAO',  0),
        ('BUZINA-INT', 'Interruptor de buzina',           'IMPORTADA',    'PADRAO',  0),
        ('GUIDAO',     'Guidão',                          'FERRAMENTARIA','PADRAO',  0),
        ('GARFO',      'Garfo',                           'FERRAMENTARIA','PADRAO',  0),
        ('BATERIA',    'Bateria',                         'IMPORTADA',    'BATERIA', 0),
        ('ENCOSTO-EST','Encosto estofado',                'IMPORTADA',    'PADRAO',  0),
        ('EIXO-DI',    'Eixo dianteiro',                  'IMPORTADA',    'PADRAO',  0),
        ('CONTROLAD',  'Controladora',                    'IMPORTADA',    'PADRAO',  0),
        ('ROLAM-GARFO','Conjunto rolamento garfo',        'IMPORTADA',    'PADRAO',  0),
        ('CON-CARREG', 'Conector cabo carregador',        'IMPORTADA',    'PADRAO',  0),
        ('CARREGADOR', 'Carregador de bateria',           'IMPORTADA',    'PADRAO',  0),
        ('BANCO-MAIS', 'Banco assento TUI MAIS',          'IMPORTADA',    'PADRAO',  0),
        ('BANCO-POP',  'Banco assento TUI POP',           'IMPORTADA',    'PADRAO',  0),
        ('ACELERADOR', 'Acelerador',                      'IMPORTADA',    'PADRAO',  0),
        ('PCARN-D',    'Pedal carona direito TUI MAIS',   'FERRAMENTARIA','PADRAO',  0),
        ('PCARN-E',    'Pedal carona esquerdo TUI MAIS',  'FERRAMENTARIA','PADRAO',  0),
        ('FUSIVEL',    'Fusível',                         'IMPORTADA',    'BATERIA', 0),
        # ── Peças novas — fase 7 ──────────────────────────────────────────
        # Globais (entram em todas as BOMs)
        ('10001',      'Farol traseiro',                  'IMPORTADA',    'PADRAO',  0),
        ('10002',      'Alarme',                          'IMPORTADA',    'PADRAO',  0),
        # Modelos -S / -LS (suspensão e variantes de quadro)
        ('10003',      'Amortecedor',                     'IMPORTADA',    'PADRAO',  0),
        ('10004',      'Garfo adaptado suspensão',        'FERRAMENTARIA','PADRAO',  0),
        ('10005',      'Quadro adaptado TUI MAIS-S',      'FERRAMENTARIA','PADRAO',  0),
        ('10006',      'Quadro adaptado TUI POP-S',       'FERRAMENTARIA','PADRAO',  0),
        ('10007',      'Quadro comprido TUI MAIS-LS',     'FERRAMENTARIA','PADRAO',  0),
        ('10008',      'Cabo freio traseiro longo',       'IMPORTADA',    'PADRAO',  0),
        # Avulsas de assistência / venda
        ('10009',      'Chave e trava painel',            'IMPORTADA',    'PADRAO',  0),
        ('10010',      'Controle de alarme',              'IMPORTADA',    'PADRAO',  0),
    ]

    for codigo, nome, origem, container_tipo, tem_var in pecas_raiz:
        cursor.execute("""
            INSERT INTO pecas
                (codigo, nome, origem, container_tipo, tem_variacao_cor, peca_pai_id)
            VALUES (%s, %s, %s, %s, %s, NULL)
            ON CONFLICT (codigo) DO NOTHING
        """, (codigo, nome, origem, container_tipo, tem_var))

    conn.commit()

    # ── Busca IDs dos kits pai ───────────────────────────────────────────────
    def _get_id(cod):
        row = cursor.execute("SELECT id FROM pecas WHERE codigo = %s", (cod,)).fetchone()
        return row['id'] if row else None

    id_freio_tras = _get_id('FREIO-TRAS')
    id_freio_di   = _get_id('FREIO-DI')
    id_rd_tras    = _get_id('RD-TRAS')
    id_rd_di      = _get_id('RD-DI')

    # ── Componentes de kits ─────────────────────────────────────────────────
    componentes = [
        # FREIO-TRAS
        ('FT-CABO',   'Cabo freio traseiro',          'IMPORTADA','PADRAO',0, id_freio_tras),
        ('FT-CILIN',  'Cilindro freio traseiro',      'IMPORTADA','PADRAO',0, id_freio_tras),
        ('FT-SENSOR', 'Sensor de freio traseiro',     'IMPORTADA','PADRAO',0, id_freio_tras),
        ('FT-PINCA',  'Pinça freio traseiro',         'IMPORTADA','PADRAO',0, id_freio_tras),
        ('FT-SUPRTE', 'Suporte retrovisor esquerdo',  'IMPORTADA','PADRAO',0, id_freio_tras),
        ('FT-PASTIL', 'Pastilha de freio traseira',   'IMPORTADA','PADRAO',0, id_freio_tras),
        ('FT-MANETE', 'Manete esquerdo',              'IMPORTADA','PADRAO',0, id_freio_tras),
        # FREIO-DI
        ('FD-CABO',   'Cabo freio dianteiro',         'IMPORTADA','PADRAO',0, id_freio_di),
        ('FD-CILIN',  'Cilindro freio dianteiro',     'IMPORTADA','PADRAO',0, id_freio_di),
        ('FD-SENSOR', 'Sensor de freio dianteiro',    'IMPORTADA','PADRAO',0, id_freio_di),
        ('FD-PINCA',  'Pinça freio dianteiro',        'IMPORTADA','PADRAO',0, id_freio_di),
        ('FD-SUPRTE', 'Suporte retrovisor direito',   'IMPORTADA','PADRAO',0, id_freio_di),
        ('FD-PASTIL', 'Pastilha de freio dianteira',  'IMPORTADA','PADRAO',0, id_freio_di),
        ('FD-MANETE', 'Manete direito',               'IMPORTADA','PADRAO',0, id_freio_di),
        # RD-TRAS
        ('RDT-PNEU',  'Pneu traseiro',               'IMPORTADA','PADRAO',0, id_rd_tras),
        ('RDT-MOTOR', 'Motor',                        'IMPORTADA','PADRAO',0, id_rd_tras),
        ('RDT-DISCO', 'Disco freio traseiro',         'IMPORTADA','PADRAO',0, id_rd_tras),
        # RD-DI
        ('RDD-PNEU',  'Pneu dianteiro',              'IMPORTADA','PADRAO',0, id_rd_di),
        ('RDD-RODA',  'Roda dianteira',              'IMPORTADA','PADRAO',0, id_rd_di),
        ('RDD-DISCO', 'Disco freio dianteiro',        'IMPORTADA','PADRAO',0, id_rd_di),
    ]

    for codigo, nome, origem, container_tipo, tem_var, pai_id in componentes:
        cursor.execute("""
            INSERT INTO pecas
                (codigo, nome, origem, container_tipo, tem_variacao_cor, peca_pai_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (codigo) DO NOTHING
        """, (codigo, nome, origem, container_tipo, tem_var, pai_id))

    conn.commit()

    # ── Inicializa estoque_pecas ─────────────────────────────────────────────
    todas = cursor.execute("SELECT id, codigo, tem_variacao_cor FROM pecas").fetchall()

    for peca in todas:
        if peca['codigo'] == 'PARALAMA':
            for cor in CORES_PARALAMA:
                cursor.execute("""
                    INSERT INTO estoque_pecas (peca_id, cor, quantidade)
                    VALUES (%s, %s, 0)
                    ON CONFLICT (peca_id, cor) DO NOTHING
                """, (peca['id'], cor))
        else:
            # ON CONFLICT casa com o índice parcial idx_ep_peca_null_cor
            # criado em criar_tabelas_pecas()
            cursor.execute("""
                INSERT INTO estoque_pecas (peca_id, cor, quantidade)
                VALUES (%s, NULL, 0)
                ON CONFLICT (peca_id) WHERE cor IS NULL DO NOTHING
            """, (peca['id'],))

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# BOM — BILL OF MATERIALS
# ──────────────────────────────────────────────

def carregar_bom_inicial():
    """
    Define quais peças compõem cada modelo de scooter.
    ON CONFLICT DO NOTHING — idempotente.
    """
    conn = get_connection()
    cursor = conn.cursor()

    def _get_peca_id(cod):
        row = cursor.execute("SELECT id FROM pecas WHERE codigo = %s", (cod,)).fetchone()
        return row['id'] if row else None

    # ── BOM TUI MAIS ────────────────────────────────────────────────────────
    # (codigo, usa_cor_scooter, cor_fixa, quantidade)
    bom_mais = [
        ('RD-TRAS',    0, None, 1),
        ('PEDAL-FD',   0, None, 1),
        ('PEDAL-FE',   0, None, 1),
        ('PARALAMA',   1, None, 1),   # usa a cor da scooter
        ('QUADRO-MAIS',0, None, 1),
        ('FREIO-TRAS', 0, None, 1),
        ('FREIO-DI',   0, None, 1),
        ('ENC-MAIS',   0, None, 1),
        ('RD-DI',      0, None, 1),
        ('PEZINHO',    0, None, 1),
        ('MOLA-PEZ',   0, None, 1),
        ('PAINEL-LCD', 0, None, 1),
        ('RETROVISOR', 0, None, 1),
        ('MESA-GUIDA', 0, None, 1),
        ('MANOPLA',    0, None, 1),
        ('BUZINA-INT', 0, None, 1),
        ('GUIDAO',     0, None, 1),
        ('GARFO',      0, None, 1),
        ('BATERIA',    0, None, 1),
        ('ENCOSTO-EST',0, None, 1),
        ('EIXO-DI',    0, None, 1),
        ('CONTROLAD',  0, None, 1),
        ('ROLAM-GARFO',0, None, 1),
        ('CON-CARREG', 0, None, 1),
        ('CARREGADOR', 0, None, 1),
        ('BANCO-MAIS', 0, None, 1),
        ('ACELERADOR', 0, None, 1),
        ('PCARN-D',    0, None, 1),
        ('PCARN-E',    0, None, 1),
    ]

    for codigo, usa_cor, cor_fixa, qtd in bom_mais:
        peca_id = _get_peca_id(codigo)
        if peca_id:
            cursor.execute("""
                INSERT INTO bom
                    (modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade)
                VALUES ('TUI MAIS', %s, %s, %s, %s)
                ON CONFLICT (modelo, peca_id) DO NOTHING
            """, (peca_id, usa_cor, cor_fixa, qtd))

    # ── BOM TUI POP ─────────────────────────────────────────────────────────
    bom_pop = [
        ('RD-TRAS',    0, None, 1),
        ('PEDAL-FD',   0, None, 1),
        ('PEDAL-FE',   0, None, 1),
        ('PARALAMA',   1, None, 1),   # usa a cor da scooter
        ('QUADRO-POP', 0, None, 1),
        ('FREIO-TRAS', 0, None, 1),
        ('FREIO-DI',   0, None, 1),
        ('ENC-POP',    0, None, 1),
        ('RD-DI',      0, None, 1),
        ('PEZINHO',    0, None, 1),
        ('MOLA-PEZ',   0, None, 1),
        ('PAINEL-LCD', 0, None, 1),
        ('RETROVISOR', 0, None, 1),
        ('MESA-GUIDA', 0, None, 1),
        ('MANOPLA',    0, None, 1),
        ('BUZINA-INT', 0, None, 1),
        ('GUIDAO',     0, None, 1),
        ('GARFO',      0, None, 1),
        ('BATERIA',    0, None, 1),
        ('ENCOSTO-EST',0, None, 1),
        ('EIXO-DI',    0, None, 1),
        ('CONTROLAD',  0, None, 1),
        ('ROLAM-GARFO',0, None, 1),
        ('CON-CARREG', 0, None, 1),
        ('CARREGADOR', 0, None, 1),
        ('BANCO-POP',  0, None, 1),
        ('ACELERADOR', 0, None, 1),
        # TUI POP não tem PCARN-D nem PCARN-E
    ]

    for codigo, usa_cor, cor_fixa, qtd in bom_pop:
        peca_id = _get_peca_id(codigo)
        if peca_id:
            cursor.execute("""
                INSERT INTO bom
                    (modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade)
                VALUES ('TUI POP', %s, %s, %s, %s)
                ON CONFLICT (modelo, peca_id) DO NOTHING
            """, (peca_id, usa_cor, cor_fixa, qtd))

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# CONSULTAS DE PEÇAS
# ──────────────────────────────────────────────

def listar_pecas(apenas_ativas=True, apenas_raiz=False):
    """Retorna lista de peças com estoque total agregado."""
    conn = get_connection()

    conditions = []
    if apenas_ativas:
        conditions.append("p.ativo = 1")
    if apenas_raiz:
        conditions.append("p.peca_pai_id IS NULL")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT p.id, p.codigo, p.nome, p.origem, p.container_tipo,
               p.tem_variacao_cor, p.peca_pai_id, p.ativo,
               p.custo_unitario,
               COALESCE(SUM(ep.quantidade), 0) AS estoque_total
        FROM pecas p
        LEFT JOIN estoque_pecas ep ON ep.peca_id = p.id
        {where}
        GROUP BY p.id
        ORDER BY p.nome
    """

    rows = [dict(row) for row in conn.execute(query).fetchall()]
    conn.close()

    for row in rows:
        row['em_critico'] = esta_em_critico(row, row['estoque_total'])

    return rows


def buscar_peca_por_codigo(codigo):
    """Retorna dict da peça ou None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM pecas WHERE codigo = %s", (codigo,)).fetchone()
    conn.close()
    return dict(row) if row else None


def buscar_peca_por_id(peca_id):
    """Retorna dict da peça ou None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM pecas WHERE id = %s", (peca_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def consultar_estoque_pecas(peca_id=None):
    """
    Retorna estoque atual por (peça, cor).
    Se peca_id informado, filtra por ele.
    """
    conn = get_connection()

    base = """
        SELECT ep.peca_id, p.codigo, p.nome, p.origem, ep.cor, ep.quantidade
        FROM estoque_pecas ep
        JOIN pecas p ON p.id = ep.peca_id
    """

    if peca_id is not None:
        rows = conn.execute(
            f"{base} WHERE ep.peca_id = %s ORDER BY ep.cor",
            (peca_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            f"{base} ORDER BY p.nome, ep.cor"
        ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def adicionar_peca(codigo, nome, origem, container_tipo='PADRAO',
                   tem_variacao_cor=False, peca_pai_id=None):
    """
    Insere nova peça. Levanta ValueError se código já existir.
    Inicializa estoque_pecas conforme tem_variacao_cor.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if cursor.execute("SELECT id FROM pecas WHERE codigo = %s", (codigo,)).fetchone():
        conn.close()
        raise ValueError(f"Código '{codigo}' já existe.")

    cursor.execute("""
        INSERT INTO pecas (codigo, nome, origem, container_tipo, tem_variacao_cor, peca_pai_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (codigo, nome, origem, container_tipo, int(tem_variacao_cor), peca_pai_id))

    nova_id = cursor.fetchone()['id']

    if tem_variacao_cor:
        for cor in CORES_PARALAMA:
            cursor.execute(
                "INSERT INTO estoque_pecas (peca_id, cor, quantidade) VALUES (%s, %s, 0) "
                "ON CONFLICT (peca_id, cor) DO NOTHING",
                (nova_id, cor)
            )
    else:
        cursor.execute(
            "INSERT INTO estoque_pecas (peca_id, cor, quantidade) VALUES (%s, NULL, 0) "
            "ON CONFLICT (peca_id) WHERE cor IS NULL DO NOTHING",
            (nova_id,)
        )

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# MOVIMENTAÇÕES
# ──────────────────────────────────────────────

def entrada_estoque_peca(peca_id, quantidade, cor=None,
                         num_lote='', motivo_detalhe=''):
    """Soma quantidade em estoque. Registra ENTRADA em movimentacoes."""
    conn = get_connection()
    cursor = conn.cursor()

    if cor:
        cursor.execute("""
            UPDATE estoque_pecas SET quantidade = quantidade + %s
            WHERE peca_id = %s AND cor = %s
        """, (quantidade, peca_id, cor))
    else:
        cursor.execute("""
            UPDATE estoque_pecas SET quantidade = quantidade + %s
            WHERE peca_id = %s AND cor IS NULL
        """, (quantidade, peca_id))

    cursor.execute("""
        INSERT INTO movimentacoes_peca
            (peca_id, cor, tipo, quantidade, motivo_detalhe, num_lote)
        VALUES (%s, %s, 'ENTRADA', %s, %s, %s)
    """, (peca_id, cor, quantidade, motivo_detalhe, num_lote))

    conn.commit()
    conn.close()


def saida_manual_peca(peca_id, quantidade, tipo, cor=None,
                      num_pedido='', motivo_detalhe='', num_lote=''):
    """
    tipo deve ser 'VENDA' ou 'DEFEITO'.
    Valida estoque suficiente — levanta ValueError se não tiver.
    """
    if tipo not in ('VENDA', 'DEFEITO', 'ASSISTENCIA'):
        raise ValueError(f"Tipo inválido: '{tipo}'. Use 'VENDA', 'DEFEITO' ou 'ASSISTENCIA'.")

    conn = get_connection()
    cursor = conn.cursor()

    if cor:
        row = cursor.execute("""
            SELECT quantidade FROM estoque_pecas WHERE peca_id = %s AND cor = %s
        """, (peca_id, cor)).fetchone()
    else:
        row = cursor.execute("""
            SELECT quantidade FROM estoque_pecas WHERE peca_id = %s AND cor IS NULL
        """, (peca_id,)).fetchone()

    if not row:
        conn.close()
        raise ValueError("Registro de estoque não encontrado para a peça/cor informada.")

    if row['quantidade'] < quantidade:
        conn.close()
        raise ValueError(
            f"Estoque insuficiente. Disponível: {row['quantidade']}, "
            f"Solicitado: {quantidade}"
        )

    if cor:
        cursor.execute("""
            UPDATE estoque_pecas SET quantidade = quantidade - %s
            WHERE peca_id = %s AND cor = %s
        """, (quantidade, peca_id, cor))
    else:
        cursor.execute("""
            UPDATE estoque_pecas SET quantidade = quantidade - %s
            WHERE peca_id = %s AND cor IS NULL
        """, (quantidade, peca_id))

    cursor.execute("""
        INSERT INTO movimentacoes_peca
            (peca_id, cor, tipo, quantidade, motivo_detalhe, num_pedido, num_lote)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (peca_id, cor, tipo, quantidade, motivo_detalhe, num_pedido, num_lote))

    conn.commit()
    conn.close()


def baixar_estoque_por_bom(modelo, cor_scooter, quantidade_scooters):
    """
    Chamado ao registrar embalagem de scooter.
    Busca BOM do modelo e consome o estoque de cada peça.
    Se ficar negativo, registra mesmo assim (alerta, não bloqueio).
    """
    conn = get_connection()
    cursor = conn.cursor()

    bom_items = cursor.execute("""
        SELECT b.peca_id, b.usa_cor_scooter, b.cor_fixa, b.quantidade
        FROM bom b
        WHERE b.modelo = %s
    """, (modelo,)).fetchall()

    for item in bom_items:
        peca_id     = item['peca_id']
        qtd_consumo = item['quantidade'] * quantidade_scooters

        if item['usa_cor_scooter']:
            cor = cor_scooter
        elif item['cor_fixa']:
            cor = item['cor_fixa']
        else:
            cor = None

        if cor:
            cursor.execute("""
                UPDATE estoque_pecas SET quantidade = quantidade - %s
                WHERE peca_id = %s AND cor = %s
            """, (qtd_consumo, peca_id, cor))
        else:
            cursor.execute("""
                UPDATE estoque_pecas SET quantidade = quantidade - %s
                WHERE peca_id = %s AND cor IS NULL
            """, (qtd_consumo, peca_id))

        cursor.execute("""
            INSERT INTO movimentacoes_peca
                (peca_id, cor, tipo, quantidade, modelo_scooter)
            VALUES (%s, %s, 'CONSUMO', %s, %s)
        """, (peca_id, cor, qtd_consumo, modelo))

    conn.commit()
    conn.close()


def existe_bom_para_modelo(modelo_nome):
    """
    Verifica dinamicamente se existe BOM cadastrada para o
    modelo (query em `bom`, não lista fixa). Usada pelo fluxo
    de produção normal (Estoque) para decidir se deve baixar
    peças automaticamente — mesmo princípio do _tem_bom()
    privado em pedido.py, mas exposta publicamente aqui.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM bom WHERE modelo = %s LIMIT 1", (modelo_nome,)
    ).fetchone()
    conn.close()
    return row is not None


# ──────────────────────────────────────────────
# RELATÓRIOS
# ──────────────────────────────────────────────

def consultar_movimentacoes(peca_id=None, tipo=None,
                            data_inicio=None, data_fim=None):
    """
    Retorna movimentações com filtros opcionais.
    JOIN com pecas para trazer nome e codigo. Ordena por data_hora DESC.
    """
    conn = get_connection()

    conditions = []
    params = []

    if peca_id:
        conditions.append("m.peca_id = %s")
        params.append(peca_id)
    if tipo:
        conditions.append("m.tipo = %s")
        params.append(tipo)
    if data_inicio:
        conditions.append("m.data_hora::date >= %s")
        params.append(data_inicio)
    if data_fim:
        conditions.append("m.data_hora::date <= %s")
        params.append(data_fim)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT m.id, m.peca_id, p.codigo, p.nome, m.cor, m.tipo,
               m.quantidade, m.motivo_detalhe, m.num_pedido, m.num_lote,
               m.modelo_scooter, to_char(m.data_hora, '{DATA_HORA_FMT}') AS data_hora
        FROM movimentacoes_peca m
        JOIN pecas p ON p.id = m.peca_id
        {where}
        ORDER BY m.data_hora DESC
    """

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _threshold_critico(peca):
    """
    Retorna o threshold de estoque crítico conforme origem e nome da peça.
    - FERRAMENTARIA (fabricada internamente, qualquer nome) → 150
    - IMPORTADA com 'paralama' no nome                       → 150
    - IMPORTADA sem 'paralama' no nome                       → 1000
    """
    nome = (peca['nome'] or '').lower()
    origem = (peca['origem'] or '').upper()
    if origem == 'FERRAMENTARIA':
        return 150
    if 'paralama' in nome:
        return 150
    return 1000  # IMPORTADA sem paralama


def esta_em_critico(peca, estoque_atual):
    """
    peca precisa ter 'origem' e 'nome'. estoque_atual é passado à parte
    porque cada consulta agrega a quantidade em estoque sob um nome de
    campo diferente (estoque_total em listar_pecas, quantidade_total em
    consultar_pecas_criticas).
    """
    return estoque_atual < _threshold_critico(peca)


def consultar_pecas_criticas():
    """
    Retorna peças em estoque crítico, conforme threshold por origem/nome
    (_threshold_critico) — não é mais um valor fixo. Agrupa por peca_id
    somando todas as cores. Cada item vem com 'threshold_critico' (usado
    pelo dashboard pra desenhar a barra proporcional ao limite da peça).
    """
    conn = get_connection()

    query = """
        SELECT ep.peca_id, p.codigo, p.nome, p.origem,
               SUM(ep.quantidade) AS quantidade_total
        FROM estoque_pecas ep
        JOIN pecas p ON p.id = ep.peca_id
        WHERE p.ativo = 1
        GROUP BY ep.peca_id, p.codigo, p.nome, p.origem
        ORDER BY quantidade_total ASC
    """

    rows = [dict(row) for row in conn.execute(query).fetchall()]
    conn.close()

    criticas = []
    for row in rows:
        if esta_em_critico(row, row['quantidade_total']):
            row['threshold_critico'] = _threshold_critico(row)
            criticas.append(row)
    return criticas


def consultar_defeitos_para_relatorio(data_inicio=None, data_fim=None):
    """
    Retorna movimentações com tipo='DEFEITO'.
    Usado para gerar relatório de reclamação ao fornecedor.
    """
    conn = get_connection()

    conditions = ["m.tipo = 'DEFEITO'"]
    params = []

    if data_inicio:
        conditions.append("m.data_hora::date >= %s")
        params.append(data_inicio)
    if data_fim:
        conditions.append("m.data_hora::date <= %s")
        params.append(data_fim)

    where = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT to_char(m.data_hora, '{DATA_HORA_FMT}') AS data_hora,
               p.codigo, p.nome, m.cor, m.quantidade,
               m.motivo_detalhe, m.num_lote
        FROM movimentacoes_peca m
        JOIN pecas p ON p.id = m.peca_id
        {where}
        ORDER BY m.data_hora DESC
    """

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ──────────────────────────────────────────────
# CUSTOS
# ──────────────────────────────────────────────

def atualizar_custo_peca(peca_id, novo_custo):
    """Atualiza o custo unitário (USD) de uma peça pelo id."""
    conn = get_connection()
    conn.execute(
        "UPDATE pecas SET custo_unitario = %s WHERE id = %s",
        (novo_custo, peca_id)
    )
    conn.commit()
    conn.close()


def atualizar_custos_iniciais():
    """
    Aplica custos unitários (USD, proforma) nas peças existentes.
    Idempotente — sobrescreve o valor atual, pode rodar múltiplas vezes.
    Imprime aviso para códigos não encontrados no banco.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # (codigo, custo_usd)
    # Sets desmembrados: RD-TRAS 70 % de 108.34, RD-DI 30 %;
    #                    FREIO-TRAS 55 % de 19.82, FREIO-DI 45 %.
    custos = [
        ('CONTROLAD',  14.38),
        ('PAINEL-LCD', 16.93),
        ('BATERIA',    10.70),
        ('ACELERADOR',  2.96),
        ('RETROVISOR',  1.82),
        ('MESA-GUIDA',  2.87),
        ('ROLAM-GARFO', 0.82),
        ('BUZINA-INT',  0.74),
        ('CON-CARREG',  0.95),
        ('EIXO-DI',     1.23),
        ('MOLA-PEZ',    0.19),
        ('BANCO-MAIS',  4.56),
        ('BANCO-POP',   4.56),
        ('ENCOSTO-EST', 1.90),
        ('CARREGADOR', 10.70),
        ('MANOPLA',     1.14),
        ('RD-TRAS',    75.84),
        ('RD-DI',      32.50),
        ('FREIO-TRAS', 10.90),
        ('FREIO-DI',    8.92),
        ('RDT-DISCO',   1.67),
        ('RDD-DISCO',   1.66),
        ('PARALAMA',    8.38),
        # Peças novas (fase 7)
        ('10001',       3.32),   # Farol traseiro
        ('10002',      16.79),   # Alarme
        ('10003',       2.35),   # Amortecedor
        ('10009',       1.00),   # Chave e trava painel
        ('10010',       0.50),   # Controle de alarme
    ]

    nao_encontrados = []
    for codigo, custo in custos:
        row = cursor.execute(
            "SELECT id FROM pecas WHERE codigo = %s", (codigo,)
        ).fetchone()
        if row:
            cursor.execute(
                "UPDATE pecas SET custo_unitario = %s WHERE id = %s",
                (custo, row['id'])
            )
        else:
            nao_encontrados.append(codigo)

    conn.commit()
    conn.close()

    if nao_encontrados:
        print(f"[AVISO] atualizar_custos_iniciais: "
              f"códigos não encontrados → {nao_encontrados}")


# ──────────────────────────────────────────────
# BOMs — MODELOS NOVOS
# ──────────────────────────────────────────────

def carregar_bom_modelos_novos():
    """
    1. Adiciona Farol traseiro + Alarme às BOMs base (TUI MAIS, TUI POP).
    2. Constrói BOMs de TUI MAIS-S, TUI POP-S e TUI MAIS-LS.
    Totalmente idempotente via ON CONFLICT DO NOTHING (UNIQUE modelo+peca_id).
    """
    conn = get_connection()
    cursor = conn.cursor()

    def _id(cod):
        row = cursor.execute(
            "SELECT id FROM pecas WHERE codigo = %s", (cod,)
        ).fetchone()
        return row['id'] if row else None

    # IDs das peças globais novas
    id_farol    = _id('10001')
    id_alarme   = _id('10002')
    id_amort    = _id('10003')
    id_garfo_s  = _id('10004')   # Garfo adaptado suspensão
    id_quad_ms  = _id('10005')   # Quadro adaptado TUI MAIS-S
    id_quad_ps  = _id('10006')   # Quadro adaptado TUI POP-S
    id_quad_ls  = _id('10007')   # Quadro comprido TUI MAIS-LS
    id_cabo_lng = _id('10008')   # Cabo freio traseiro longo

    # IDs das peças originais que serão substituídas nas variantes
    id_quadro_mais = _id('QUADRO-MAIS')
    id_quadro_pop  = _id('QUADRO-POP')
    id_garfo_orig  = _id('GARFO')

    # ── 5.1 Adicionar Farol + Alarme às BOMs base ───────────────────────────
    for modelo in ('TUI MAIS', 'TUI POP'):
        for peca_id in (id_farol, id_alarme):
            if peca_id:
                cursor.execute("""
                    INSERT INTO bom
                        (modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade)
                    VALUES (%s, %s, 0, NULL, 1)
                    ON CONFLICT (modelo, peca_id) DO NOTHING
                """, (modelo, peca_id))

    # ── 5.2 BOM TUI MAIS-S ──────────────────────────────────────────────────
    # Cópia de TUI MAIS (já com farol+alarme), exceto QUADRO-MAIS e GARFO;
    # adiciona Garfo adaptado, Quadro MAIS-S e Amortecedor x4.
    excluir_mais_s = {id_quadro_mais, id_garfo_orig}
    for item in cursor.execute(
        "SELECT peca_id, usa_cor_scooter, cor_fixa, quantidade "
        "FROM bom WHERE modelo = 'TUI MAIS'"
    ).fetchall():
        if item['peca_id'] not in excluir_mais_s:
            cursor.execute("""
                INSERT INTO bom
                    (modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade)
                VALUES ('TUI MAIS-S', %s, %s, %s, %s)
                ON CONFLICT (modelo, peca_id) DO NOTHING
            """, (item['peca_id'], item['usa_cor_scooter'],
                  item['cor_fixa'], item['quantidade']))

    for peca_id, qtd in [(id_garfo_s, 1), (id_quad_ms, 1), (id_amort, 4)]:
        if peca_id:
            cursor.execute("""
                INSERT INTO bom
                    (modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade)
                VALUES ('TUI MAIS-S', %s, 0, NULL, %s)
                ON CONFLICT (modelo, peca_id) DO NOTHING
            """, (peca_id, qtd))

    # ── 5.3 BOM TUI POP-S ───────────────────────────────────────────────────
    # Cópia de TUI POP (já com farol+alarme), exceto QUADRO-POP e GARFO;
    # adiciona Garfo adaptado, Quadro POP-S e Amortecedor x4.
    excluir_pop_s = {id_quadro_pop, id_garfo_orig}
    for item in cursor.execute(
        "SELECT peca_id, usa_cor_scooter, cor_fixa, quantidade "
        "FROM bom WHERE modelo = 'TUI POP'"
    ).fetchall():
        if item['peca_id'] not in excluir_pop_s:
            cursor.execute("""
                INSERT INTO bom
                    (modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade)
                VALUES ('TUI POP-S', %s, %s, %s, %s)
                ON CONFLICT (modelo, peca_id) DO NOTHING
            """, (item['peca_id'], item['usa_cor_scooter'],
                  item['cor_fixa'], item['quantidade']))

    for peca_id, qtd in [(id_garfo_s, 1), (id_quad_ps, 1), (id_amort, 4)]:
        if peca_id:
            cursor.execute("""
                INSERT INTO bom
                    (modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade)
                VALUES ('TUI POP-S', %s, 0, NULL, %s)
                ON CONFLICT (modelo, peca_id) DO NOTHING
            """, (peca_id, qtd))

    # ── 5.4 BOM TUI MAIS-LS ─────────────────────────────────────────────────
    # Cópia de TUI MAIS-S, exceto Quadro MAIS-S (→ Quadro comprido LS).
    # FREIO-TRAS permanece; Cabo freio longo é adicionado como item EXTRA —
    # a substituição precisa do cabo dentro do kit será refinada quando
    # os componentes de kit forem detalhados individualmente na BOM.
    for item in cursor.execute(
        "SELECT peca_id, usa_cor_scooter, cor_fixa, quantidade "
        "FROM bom WHERE modelo = 'TUI MAIS-S'"
    ).fetchall():
        if item['peca_id'] == id_quad_ms:
            continue  # substituído por Quadro comprido LS
        cursor.execute("""
            INSERT INTO bom
                (modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade)
            VALUES ('TUI MAIS-LS', %s, %s, %s, %s)
            ON CONFLICT (modelo, peca_id) DO NOTHING
        """, (item['peca_id'], item['usa_cor_scooter'],
              item['cor_fixa'], item['quantidade']))

    for peca_id, qtd in [(id_quad_ls, 1), (id_cabo_lng, 1)]:
        if peca_id:
            cursor.execute("""
                INSERT INTO bom
                    (modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade)
                VALUES ('TUI MAIS-LS', %s, 0, NULL, %s)
                ON CONFLICT (modelo, peca_id) DO NOTHING
            """, (peca_id, qtd))

    conn.commit()
    conn.close()
