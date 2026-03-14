import sqlite3
import os
import streamlit as st


class CachedConnection:
    """
    Wrapper usado SOMENTE para SQLite cacheado.
    No SQLite, ignorar close() ajuda no desempenho com Streamlit.
    """
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        # Para SQLite cacheado, ignoramos o fechamento
        pass

    def __getattr__(self, name):
        return getattr(self._conn, name)


def eh_postgres(db_ref: str) -> bool:
    return isinstance(db_ref, str) and (
        db_ref.startswith("postgresql://") or db_ref.startswith("postgres://")
    )


# =========================================================
# SQLITE CACHEADO
# =========================================================
@st.cache_resource(show_spinner=False)
def _get_sqlite_persistente(nome_db):
    # Garante pasta local se vier só nome de arquivo
    if nome_db and not os.path.isabs(nome_db):
        pasta = os.path.dirname(nome_db)
        if pasta:
            os.makedirs(pasta, exist_ok=True)

    conn = sqlite3.connect(nome_db, check_same_thread=False)
    return conn


def conectar_banco(nome_db):
    """
    Retorna (conn, engine)

    - Postgres: conexão NOVA a cada chamada
    - SQLite: conexão cacheada
    """
    if eh_postgres(nome_db):
        import psycopg2

        conn = psycopg2.connect(
            nome_db,
            sslmode="require",
            connect_timeout=10
        )
        return conn, "postgres"

    conn_sqlite = _get_sqlite_persistente(nome_db)
    return CachedConnection(conn_sqlite), "sqlite"


def inicializar_banco(nome_db):
    """
    Cria as tabelas se elas não existirem.
    """
    conn, engine = conectar_banco(nome_db)
    cursor = None

    try:
        cursor = conn.cursor()

        if engine == "postgres":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    tipo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    valor DOUBLE PRECISION NOT NULL,
                    data_prevista DATE NOT NULL,
                    data_real DATE,
                    status TEXT NOT NULL,
                    conta_id INTEGER,
                    categoria_id INTEGER,
                    FOREIGN KEY (conta_id) REFERENCES accounts(id),
                    FOREIGN KEY (categoria_id) REFERENCES categories(id)
                )
            """)

        else:  # sqlite
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_prevista DATE NOT NULL,
                    data_real DATE,
                    status TEXT NOT NULL,
                    conta_id INTEGER,
                    categoria_id INTEGER,
                    FOREIGN KEY (conta_id) REFERENCES accounts(id),
                    FOREIGN KEY (categoria_id) REFERENCES categories(id)
                )
            """)

        conn.commit()

    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        try:
            conn.close()
        except Exception:
            pass
