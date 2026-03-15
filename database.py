import os
import sqlite3
import streamlit as st


# =========================================================
# WRAPPERS DE CONEXÃO
# =========================================================
class CachedSQLiteConnection:
    """
    Wrapper usado no SQLite cacheado.
    No SQLite local, ignorar close() ajuda no desempenho com Streamlit.
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
        # No SQLite cacheado, não fechamos de verdade
        pass

    def __getattr__(self, name):
        return getattr(self._conn, name)


class PooledPostgresConnection:
    """
    Wrapper da conexão do Postgres.
    Ao dar close(), a conexão volta para o pool em vez de ser destruída.
    """
    def __init__(self, conn, pool=None):
        self._conn = conn
        self._pool = pool
        self._closed = False

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        if self._closed:
            return

        try:
            if self._pool is not None:
                # devolve ao pool
                self._pool.putconn(self._conn)
            else:
                self._conn.close()
        finally:
            self._closed = True

    def __getattr__(self, name):
        return getattr(self._conn, name)


# =========================================================
# DETECÇÃO DE BANCO
# =========================================================
def eh_postgres(db_ref: str) -> bool:
    return isinstance(db_ref, str) and (
        db_ref.startswith("postgresql://") or db_ref.startswith("postgres://")
    )


# =========================================================
# SQLITE CACHEADO
# =========================================================
@st.cache_resource(show_spinner=False)
def _get_sqlite_persistente(nome_db):
    # Se vier caminho relativo com pasta, garante que a pasta exista
    if nome_db and not os.path.isabs(nome_db):
        pasta = os.path.dirname(nome_db)
        if pasta:
            os.makedirs(pasta, exist_ok=True)

    conn = sqlite3.connect(nome_db, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


# =========================================================
# POSTGRES / NEON COM POOL
# =========================================================
@st.cache_resource(show_spinner=False)
def _get_postgres_pool(nome_db):
    """
    Cria um pool de conexões para o Postgres/Neon.
    Isso ajuda bastante na performance em apps Streamlit.
    """
    import psycopg2
    from psycopg2.pool import SimpleConnectionPool

    pool = SimpleConnectionPool(
        minconn=1,
        maxconn=5,
        dsn=nome_db,
        sslmode="require",
        connect_timeout=10,
        application_name="DTech_Streamlit",
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )
    return pool


def _validar_conn_postgres(conn) -> bool:
    """
    Faz um teste leve pra garantir que a conexão ainda está viva.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True
    except Exception:
        return False
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass


def conectar_banco(nome_db):
    """
    Retorna:
      - (conn, "postgres") para Neon/Postgres
      - (conn, "sqlite") para SQLite
    Mantém compatibilidade com seu código atual.
    """
    if eh_postgres(nome_db):
        import psycopg2

        pool = _get_postgres_pool(nome_db)
        conn = None

        try:
            conn = pool.getconn()

            # valida se veio viva do pool
            if not _validar_conn_postgres(conn):
                try:
                    conn.close()
                except Exception:
                    pass
                conn = psycopg2.connect(
                    nome_db,
                    sslmode="require",
                    connect_timeout=10,
                    application_name="DTech_Streamlit_Fallback",
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5,
                )
                return PooledPostgresConnection(conn, pool=None), "postgres"

            return PooledPostgresConnection(conn, pool=pool), "postgres"

        except Exception:
            # fallback: conexão direta se o pool falhar
            conn = psycopg2.connect(
                nome_db,
                sslmode="require",
                connect_timeout=10,
                application_name="DTech_Streamlit_Fallback",
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
            )
            return PooledPostgresConnection(conn, pool=None), "postgres"

    # SQLite
    conn_sqlite = _get_sqlite_persistente(nome_db)
    return CachedSQLiteConnection(conn_sqlite), "sqlite"


# =========================================================
# INICIALIZAÇÃO DO BANCO
# =========================================================
def inicializar_banco(nome_db):
    conn, engine = conectar_banco(nome_db)
    cursor = None

    try:
        cursor = conn.cursor()

        if engine == "postgres":
            # -------------------------
            # Tabelas principais
            # -------------------------
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    usuario_dono TEXT DEFAULT 'danilo'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    usuario_dono TEXT DEFAULT 'danilo'
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
                    usuario_dono TEXT DEFAULT 'danilo',
                    FOREIGN KEY (conta_id) REFERENCES accounts(id),
                    FOREIGN KEY (categoria_id) REFERENCES categories(id)
                )
            """)

            # -------------------------
            # Garante coluna usuario_dono
            # -------------------------
            cursor.execute("""
                ALTER TABLE accounts
                ADD COLUMN IF NOT EXISTS usuario_dono TEXT DEFAULT 'danilo'
            """)
            cursor.execute("""
                ALTER TABLE categories
                ADD COLUMN IF NOT EXISTS usuario_dono TEXT DEFAULT 'danilo'
            """)
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN IF NOT EXISTS usuario_dono TEXT DEFAULT 'danilo'
            """)

            # -------------------------
            # Corrige dados antigos vazios
            # -------------------------
            cursor.execute("""
                UPDATE accounts
                SET usuario_dono = 'danilo'
                WHERE usuario_dono IS NULL OR usuario_dono = ''
            """)
            cursor.execute("""
                UPDATE categories
                SET usuario_dono = 'danilo'
                WHERE usuario_dono IS NULL OR usuario_dono = ''
            """)
            cursor.execute("""
                UPDATE transactions
                SET usuario_dono = 'danilo'
                WHERE usuario_dono IS NULL OR usuario_dono = ''
            """)

            # -------------------------
            # Índices úteis para performance
            # -------------------------
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_accounts_usuario_dono
                ON accounts (usuario_dono)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_categories_usuario_dono
                ON categories (usuario_dono)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_usuario_dono
                ON transactions (usuario_dono)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_data_prevista
                ON transactions (data_prevista)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_status
                ON transactions (status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_conta_id
                ON transactions (conta_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_categoria_id
                ON transactions (categoria_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_usuario_data
                ON transactions (usuario_dono, data_prevista)
            """)

        else:
            # -------------------------
            # SQLite - tabelas principais
            # -------------------------
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    usuario_dono TEXT DEFAULT 'danilo'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    usuario_dono TEXT DEFAULT 'danilo'
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
                    usuario_dono TEXT DEFAULT 'danilo',
                    FOREIGN KEY (conta_id) REFERENCES accounts(id),
                    FOREIGN KEY (categoria_id) REFERENCES categories(id)
                )
            """)

            # Garante coluna usuario_dono sem quebrar se já existir
            for tabela in ["accounts", "categories", "transactions"]:
                try:
                    cursor.execute(
                        f"ALTER TABLE {tabela} ADD COLUMN usuario_dono TEXT DEFAULT 'danilo'"
                    )
                except Exception:
                    pass

            # Corrige dados antigos vazios
            for tabela in ["accounts", "categories", "transactions"]:
                cursor.execute(f"""
                    UPDATE {tabela}
                    SET usuario_dono = 'danilo'
                    WHERE usuario_dono IS NULL OR usuario_dono = ''
                """)

            # Índices úteis
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_accounts_usuario_dono
                ON accounts (usuario_dono)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_categories_usuario_dono
                ON categories (usuario_dono)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_usuario_dono
                ON transactions (usuario_dono)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_data_prevista
                ON transactions (data_prevista)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_status
                ON transactions (status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_conta_id
                ON transactions (conta_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_categoria_id
                ON transactions (categoria_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_usuario_data
                ON transactions (usuario_dono, data_prevista)
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
