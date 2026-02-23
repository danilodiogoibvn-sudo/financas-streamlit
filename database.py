import sqlite3
import os

def eh_postgres(db_ref: str) -> bool:
    return isinstance(db_ref, str) and (
        db_ref.startswith("postgresql://") or db_ref.startswith("postgres://")
    )

def conectar_banco(nome_db):
    """
    Retorna (conn, engine)
    engine = 'postgres' | 'sqlite'
    """
    if eh_postgres(nome_db):
        import psycopg2
        conn = psycopg2.connect(nome_db, sslmode="require")
        return conn, "postgres"

    # garante pasta local se vier só nome de arquivo
    if nome_db and not os.path.isabs(nome_db):
        pasta = os.path.dirname(nome_db)
        if pasta:
            os.makedirs(pasta, exist_ok=True)

    conn = sqlite3.connect(nome_db)
    return conn, "sqlite"


def inicializar_banco(nome_db):
    """
    Compatível com:
    - SQLite (local): nome_db = "financas.db" ou "data/financas.db"
    - Postgres/Neon (cloud): nome_db = "postgresql://..."
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
    conn.close()
