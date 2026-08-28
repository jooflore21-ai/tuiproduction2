"""
Migração SQLite -> PostgreSQL (Fase 0).

Cria as 12 tabelas reais do estoque.db no Postgres (schema nativo,
FKs preservadas), copia todos os dados e valida que as contagens
batem. Idempotente: TRUNCATE ... RESTART IDENTITY CASCADE antes de
cada carga, então pode ser executado quantas vezes for preciso sem
duplicar dados.

Uso:
    python app/migrate_to_postgres.py
"""
import sqlite3
import sys

from app.models.connection import get_connection

NOME_BANCO_SQLITE = "estoque.db"

# Ordem de criação/carga respeitando dependências de FK.
TABELAS_EM_ORDEM = [
    "edicoes",
    "produtos",
    "pecas",
    "variacoes",
    "producao",
    "assistencia",
    "saidas_estoque",
    "estoque_pecas",
    "movimentacoes_peca",
    "bom",
    "pedidos",
    "itens_pedido_scooter",
]

DDL = """
CREATE TABLE IF NOT EXISTS edicoes (
    id SERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
    id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pecas (
    id SERIAL PRIMARY KEY,
    codigo TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    origem TEXT NOT NULL,
    container_tipo TEXT DEFAULT 'PADRAO',
    tem_variacao_cor INTEGER DEFAULT 0,
    peca_pai_id INTEGER REFERENCES pecas(id),
    ativo INTEGER DEFAULT 1,
    custo_unitario REAL DEFAULT 0
);

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

CREATE TABLE IF NOT EXISTS producao (
    id SERIAL PRIMARY KEY,
    variacao_id INTEGER NOT NULL REFERENCES variacoes(id),
    quantidade INTEGER NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assistencia (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    quantidade INTEGER NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saidas_estoque (
    id SERIAL PRIMARY KEY,
    variacao_id INTEGER NOT NULL REFERENCES variacoes(id),
    quantidade INTEGER NOT NULL,
    motivo TEXT NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observacao TEXT,
    num_pedido TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS estoque_pecas (
    id SERIAL PRIMARY KEY,
    peca_id INTEGER NOT NULL REFERENCES pecas(id),
    cor TEXT DEFAULT NULL,
    quantidade INTEGER NOT NULL DEFAULT 0,
    UNIQUE(peca_id, cor)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ep_peca_null_cor
    ON estoque_pecas(peca_id) WHERE cor IS NULL;

CREATE TABLE IF NOT EXISTS movimentacoes_peca (
    id SERIAL PRIMARY KEY,
    peca_id INTEGER NOT NULL REFERENCES pecas(id),
    cor TEXT DEFAULT NULL,
    tipo TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    motivo_detalhe TEXT DEFAULT '',
    num_pedido TEXT DEFAULT '',
    num_lote TEXT DEFAULT '',
    modelo_scooter TEXT DEFAULT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bom (
    id SERIAL PRIMARY KEY,
    modelo TEXT NOT NULL,
    peca_id INTEGER NOT NULL REFERENCES pecas(id),
    usa_cor_scooter INTEGER DEFAULT 0,
    cor_fixa TEXT DEFAULT NULL,
    quantidade INTEGER NOT NULL DEFAULT 1,
    UNIQUE(modelo, peca_id)
);

CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    num_pedido TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'RESERVADO',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_despacho TIMESTAMP DEFAULT NULL,
    prioridade TEXT DEFAULT 'MEDIA',
    transportadora TEXT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS itens_pedido_scooter (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
    variacao_id INTEGER NOT NULL REFERENCES variacoes(id),
    producao_id INTEGER REFERENCES producao(id),
    quantidade INTEGER NOT NULL
);
"""


def get_sqlite_connection():
    conn = sqlite3.connect(NOME_BANCO_SQLITE)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas_postgres():
    print("== Criando tabelas no PostgreSQL ==")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(DDL)
    conn.commit()
    conn.close()
    for tabela in TABELAS_EM_ORDEM:
        print(f"  ok: {tabela}")


def migrar_dados_sqlite_para_postgres():
    print("\n== Migrando dados do SQLite para o PostgreSQL ==")
    sqlite_conn = get_sqlite_connection()
    pg_conn = get_connection()
    cursor = pg_conn.cursor()

    # TRUNCATE de todas as tabelas de uma vez (CASCADE resolve a
    # ordem de FK sozinho) — torna a migração idempotente.
    tabelas_sql = ", ".join(TABELAS_EM_ORDEM)
    cursor.execute(f"TRUNCATE TABLE {tabelas_sql} RESTART IDENTITY CASCADE")

    resultado = {}
    for tabela in TABELAS_EM_ORDEM:
        sqlite_cursor = sqlite_conn.execute(f"SELECT * FROM {tabela} ORDER BY id")
        colunas = [d[0] for d in sqlite_cursor.description]
        linhas = sqlite_cursor.fetchall()

        if linhas:
            cols_sql = ", ".join(colunas)
            placeholders = ", ".join(["%s"] * len(colunas))
            insert_sql = f"INSERT INTO {tabela} ({cols_sql}) VALUES ({placeholders})"
            for linha in linhas:
                cursor.execute(insert_sql, tuple(linha[c] for c in colunas))

            # Realinha a sequence do SERIAL com o maior id inserido,
            # já que os ids foram inseridos explicitamente.
            cursor.execute(
                f"SELECT setval(pg_get_serial_sequence(%s, 'id'), "
                f"(SELECT MAX(id) FROM {tabela}))",
                (tabela,),
            )

        resultado[tabela] = len(linhas)
        print(f"  {tabela}: {len(linhas)} linha(s) migrada(s)")

    pg_conn.commit()
    pg_conn.close()
    sqlite_conn.close()
    return resultado


def validar_migracao():
    print("\n== Validando migração ==")
    sqlite_conn = get_sqlite_connection()
    pg_conn = get_connection()
    cursor = pg_conn.cursor()

    tudo_ok = True
    for tabela in TABELAS_EM_ORDEM:
        count_sqlite = sqlite_conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) AS n FROM {tabela}")
        count_pg = cursor.fetchone()["n"]

        status = "OK" if count_sqlite == count_pg else "DIVERGENTE"
        if count_sqlite != count_pg:
            tudo_ok = False
        print(f"  {tabela}: sqlite={count_sqlite} postgres={count_pg} [{status}]")

    # Query real: confirma que os dados voltam como dict (RealDictCursor-like)
    cursor.execute("SELECT * FROM variacoes LIMIT 1")
    linha = cursor.fetchone()
    if linha is not None and not isinstance(linha, dict):
        print("  [ERRO] linha retornada não é dict:", type(linha))
        tudo_ok = False
    else:
        print(f"  amostra variacoes[0] é dict: {isinstance(linha, dict)}")

    pg_conn.close()
    sqlite_conn.close()

    if tudo_ok:
        print("\nMigração validada com sucesso.")
    else:
        print("\n[ATENÇÃO] Divergências encontradas — revisar antes de prosseguir.")
    return tudo_ok


if __name__ == "__main__":
    try:
        criar_tabelas_postgres()
        migrar_dados_sqlite_para_postgres()
        ok = validar_migracao()
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"\n[ERRO] Migração falhou: {e}")
        sys.exit(1)
