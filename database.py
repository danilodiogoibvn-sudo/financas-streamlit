import sqlite3

def inicializar_banco(nome_db):
    """
    Compatível com:
    - SQLite (local): nome_db = "financas.db"
    - Postgres/Neon (cloud): nome_db = "postgresql://user:pass@host/dbname?sslmode=require"
    """

    # Detecta Postgres via URL
    is_postgres = isinstance(nome_db, str) and (
        nome_db.startswith("postgresql://") or nome_db.startswith("postgres://")
    )

    if is_postgres:
        import psycopg2
        conn = psycopg2.connect(nome_db)
        cursor = conn.cursor()

        # Postgres: SERIAL em vez de AUTOINCREMENT e tipos compatíveis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL
            )
        ''')

        cursor.execute('''
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
                FOREIGN KEY(conta_id) REFERENCES accounts(id),
                FOREIGN KEY(categoria_id) REFERENCES categories(id)
            )
        ''')

        conn.commit()
        conn.close()
        return

    # SQLite (local)
    conn = sqlite3.connect(nome_db)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    ''')

    cursor.execute('''
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
            FOREIGN KEY(conta_id) REFERENCES accounts(id),
            FOREIGN KEY(categoria_id) REFERENCES categories(id)
        )
    ''')

    conn.commit()
    conn.close()
