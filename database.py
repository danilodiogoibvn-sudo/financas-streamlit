import sqlite3
import os
import streamlit as st

class CachedConnection:
    """
    Um 'disfarce' para a conexão que impede o sistema de fechá-la.
    Isso engana o conn.close() das outras páginas para manter a conexão viva no cache.
    """
    def __init__(self, conn):
        self._conn = conn
        
    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)
        
    def commit(self):
        self._conn.commit()
        
    def rollback(self):
        self._conn.rollback()
        
    def close(self):
        pass # A MÁGICA ACONTECE AQUI! Ignora o fechamento para manter o cache voando.
        
    def __getattr__(self, name):
        # Repassa qualquer outra chamada do Pandas direto para a conexão original
        return getattr(self._conn, name)

def eh_postgres(db_ref: str) -> bool:
    return isinstance(db_ref, str) and (
        db_ref.startswith("postgresql://") or db_ref.startswith("postgres://")
    )

# 🚀 O PODER DO STREAMLIT: Guarda a conexão na memória do servidor!
@st.cache_resource(show_spinner=False)
def _get_conexao_persistente(nome_db):
    if eh_postgres(nome_db):
        import psycopg2
        conn = psycopg2.connect(nome_db, sslmode="require")
        return conn, "postgres"

    # Garante pasta local se vier só nome de arquivo (para SQLite)
    if nome_db and not os.path.isabs(nome_db):
        pasta = os.path.dirname(nome_db)
        if pasta:
            os.makedirs(pasta, exist_ok=True)

    # check_same_thread=False é obrigatório para usar SQLite com cache no Streamlit
    conn = sqlite3.connect(nome_db, check_same_thread=False)
    return conn, "sqlite"


def conectar_banco(nome_db):
    """
    Retorna (conn, engine)
    conn é envelopado na nossa classe mágica para não fechar nunca.
    """
    conn_real, engine = _get_conexao_persistente(nome_db)
    return CachedConnection(conn_real), engine


def inicializar_banco(nome_db):
    """
    Cria as tabelas se elas não existirem.
    """
    conn, engine = conectar_banco(nome_db)
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
    # Aqui o conn.close() vai ser chamado, mas o nosso disfarce vai ignorar lindamente!
    conn.close()
