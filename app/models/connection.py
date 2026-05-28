import sqlite3

NOME_BANCO_DE_DADOS = "estoque.db"


def get_connection():
    conn = sqlite3.connect(NOME_BANCO_DE_DADOS)
    conn.row_factory = sqlite3.Row
    return conn
