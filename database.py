import sqlite3

def inicializar_banco(nome_db):
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