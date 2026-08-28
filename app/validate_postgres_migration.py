"""
Validação pós-migração SQLite -> PostgreSQL (Fase 0).

Usa o test_client do Flask (não sobe servidor de verdade) para
checar que as rotas respondem 200 contra o Postgres, e compara
contagens de linhas com o estoque.db original.

Uso:
    python app/validate_postgres_migration.py
"""
import sqlite3
import sys

from app import create_app
from app.models.connection import get_connection

NOME_BANCO_SQLITE = "estoque.db"

ROTAS = ["/", "/estoque_geral", "/producao", "/pecas", "/saidas"]

TABELAS_PARA_COMPARAR = ["variacoes", "pedidos", "producao"]


def checar_rotas():
    print("== Checando rotas (via test_client) ==")
    app = create_app()
    client = app.test_client()

    tudo_ok = True
    for rota in ROTAS:
        resp = client.get(rota)
        status = "OK" if resp.status_code == 200 else "FALHOU"
        if resp.status_code != 200:
            tudo_ok = False
        print(f"  GET {rota} -> {resp.status_code} [{status}]")

    return tudo_ok


def checar_contagens():
    print("\n== Comparando contagens SQLite x PostgreSQL ==")
    sqlite_conn = sqlite3.connect(NOME_BANCO_SQLITE)
    pg_conn = get_connection()
    cursor = pg_conn.cursor()

    tudo_ok = True
    for tabela in TABELAS_PARA_COMPARAR:
        count_sqlite = sqlite_conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) AS n FROM {tabela}")
        count_pg = cursor.fetchone()["n"]

        status = "OK" if count_sqlite == count_pg else "DIVERGENTE"
        if count_sqlite != count_pg:
            tudo_ok = False
        print(f"  {tabela}: sqlite={count_sqlite} postgres={count_pg} [{status}]")

    sqlite_conn.close()
    pg_conn.close()
    return tudo_ok


def checar_query_real():
    print("\n== Checando query real (SELECT * FROM variacoes LIMIT 1) ==")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM variacoes LIMIT 1")
    linha = cursor.fetchone()
    conn.close()

    if linha is None:
        print("  [AVISO] tabela variacoes vazia — não é possível checar o tipo.")
        return True

    ok = isinstance(linha, dict)
    print(f"  tipo retornado: {type(linha).__name__} -> é dict: {ok}")
    return ok


if __name__ == "__main__":
    try:
        ok_rotas = checar_rotas()
        ok_contagens = checar_contagens()
        ok_query = checar_query_real()

        print("\n== Resumo ==")
        print(f"  Rotas 200:        {'OK' if ok_rotas else 'FALHOU'}")
        print(f"  Contagens batem:  {'OK' if ok_contagens else 'FALHOU'}")
        print(f"  Query retorna dict: {'OK' if ok_query else 'FALHOU'}")

        sys.exit(0 if (ok_rotas and ok_contagens and ok_query) else 1)
    except Exception as e:
        print(f"\n[ERRO] Validação falhou: {e}")
        sys.exit(1)
