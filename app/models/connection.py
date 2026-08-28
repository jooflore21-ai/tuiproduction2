import os

import psycopg
from psycopg import OperationalError
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """
    Abre uma conexão com o PostgreSQL.
    row_factory=dict_row → linhas viram dict (equivalente ao
    sqlite3.Row usado antes: suporta row['coluna']).
    autocommit=False → cada função de model controla sua própria
    transação via conn.commit() (mesmo padrão já usado no projeto).
    """
    if not DATABASE_URL:
        raise ConnectionError(
            "DATABASE_URL não definida. Configure o arquivo .env na raiz "
            "do projeto (ex.: DATABASE_URL=postgresql://usuario:senha@localhost:5432/banco)."
        )
    try:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=False)
    except OperationalError as e:
        raise ConnectionError(f"Falha ao conectar ao PostgreSQL: {e}") from e
