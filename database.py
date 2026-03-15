import sqlite3
import os
import streamlit as st

class CachedConnection:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        pass

    def __getattr__(self, name):
        return getattr(self._conn, name)

def eh_postgres(db_ref: str) -> bool:
    return isinstance(db_ref, str) and (
        db_ref.startswith("postgresql://") or db_ref.startswith("postgres://")
    )

@st.cache_resource(show_spinner=False)
def _get_sqlite_persistente(nome_db):
    if nome_db and not os.path.isabs(nome_db):
        pasta = os.path.dirname(nome_db)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
    conn = sqlite3.connect(nome_db, check_same_thread=False)
    return conn

def conectar_banco(nome_db):
    if eh_postgres(nome_db):
        import psycopg2
        conn = psycopg2.connect(nome_db, sslmode="require", connect_timeout=10)
        return conn, "postgres"
    conn_sqlite = _get_sqlite_persistente(nome_db)
    return CachedConnection(conn_sqlite), "sqlite"

def inicializar_banco(nome_db):
    conn, engine = conectar_banco(nome_db)
    cursor = None
    try:
        cursor = conn.cursor()

        if engine == "postgres":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id SERIAL PRIMARY KEY, nome TEXT NOT NULL, tipo TEXT NOT NULL, usuario_dono TEXT DEFAULT 'danilo'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY, nome TEXT NOT NULL, tipo TEXT NOT NULL, usuario_dono TEXT DEFAULT 'danilo'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY, tipo TEXT NOT NULL, descricao TEXT NOT NULL, valor DOUBLE PRECISION NOT NULL, 
                    data_prevista DATE NOT NULL, data_real DATE, status TEXT NOT NULL, conta_id INTEGER, categoria_id INTEGER, 
                    usuario_dono TEXT DEFAULT 'danilo',
                    FOREIGN KEY (conta_id) REFERENCES accounts(id), FOREIGN KEY (categoria_id) REFERENCES categories(id)
                )
            """)
            
            cursor.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS usuario_dono TEXT DEFAULT 'danilo'")
            cursor.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS usuario_dono TEXT DEFAULT 'danilo'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS usuario_dono TEXT DEFAULT 'danilo'")
            
            # 🚀 A VACINA: Força a etiqueta 'danilo' em tudo que ficou vazio no passado!
            cursor.execute("UPDATE accounts SET usuario_dono = 'danilo' WHERE usuario_dono IS NULL OR usuario_dono = ''")
            cursor.execute("UPDATE categories SET usuario_dono = 'danilo' WHERE usuario_dono IS NULL OR usuario_dono = ''")
            cursor.execute("UPDATE transactions SET usuario_dono = 'danilo' WHERE usuario_dono IS NULL OR usuario_dono = ''")

        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, tipo TEXT NOT NULL, usuario_dono TEXT DEFAULT 'danilo'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, tipo TEXT NOT NULL, usuario_dono TEXT DEFAULT 'danilo'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL, descricao TEXT NOT NULL, valor REAL NOT NULL, 
                    data_prevista DATE NOT NULL, data_real DATE, status TEXT NOT NULL, conta_id INTEGER, categoria_id INTEGER, 
                    usuario_dono TEXT DEFAULT 'danilo',
                    FOREIGN KEY (conta_id) REFERENCES accounts(id), FOREIGN KEY (categoria_id) REFERENCES categories(id)
                )
            """)
            
            for tabela in ["accounts", "categories", "transactions"]:
                try:
                    cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN usuario_dono TEXT DEFAULT 'danilo'")
                except Exception:
                    pass
            
            # 🚀 VACINA PARA SQLITE TAMBÉM
            for tabela in ["accounts", "categories", "transactions"]:
                cursor.execute(f"UPDATE {tabela} SET usuario_dono = 'danilo' WHERE usuario_dono IS NULL OR usuario_dono = ''")

        conn.commit()
    except Exception:
        try: conn.rollback()
        except Exception: pass
        raise
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        try: conn.close()
        except Exception: pass
