import streamlit as st
import sqlite3
import os
from database import inicializar_banco


# ----------------------------
# LOGOUT (para usar nas páginas)
# ----------------------------
def fazer_logout():
    for k in [
        "autenticado",
        "db_nome",
        "empresa",
        "usuario_atual",
        "senha_recem_criada",
        "login_user_candidate",
        "mostrar_criar_senha",
        "empresa_tmp",
        "db_tmp",
    ]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


# ----------------------------
# Guard / páginas internas
# ----------------------------
def exigir_login():
    """
    Use nas outras páginas:
    - Não mostra tela de login
    - Se não estiver logado, trava acesso
    """
    if st.session_state.get("autenticado"):
        return

    st.warning("Você precisa fazer login na Home para acessar esta página.")
    st.stop()


# ----------------------------
# Conexão com o cofre de usuários (admin)
# ----------------------------
def conectar_admin():
    db_url = os.getenv("DATABASE_URL", "").strip()
    usando_postgres = bool(db_url)

    if usando_postgres:
        import psycopg2
        conn = psycopg2.connect(
            db_url,
            sslmode="require",
            connect_timeout=10
        )
        return conn

    conn = sqlite3.connect("admin.db")
    return conn


# ----------------------------
# Garante tabela de usuários
# ----------------------------
def preparar_admin(conn, usando_postgres, db_url):
    cursor = conn.cursor()

    try:
        if usando_postgres:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    usuario TEXT PRIMARY KEY,
                    senha TEXT,
                    db_nome TEXT,
                    empresa TEXT,
                    ativo INTEGER DEFAULT 1
                )
                """
            )

            cursor.execute(
                "SELECT usuario FROM usuarios WHERE usuario=%s",
                ("danilo",)
            )
            existe = cursor.fetchone()

            if not existe:
                cursor.execute(
                    """
                    INSERT INTO usuarios (usuario, senha, db_nome, empresa, ativo)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    ("danilo", "09011998Dan*", db_url, "D.Tech - Danilo Diogo", 1),
                )

            cursor.execute(
                "UPDATE usuarios SET empresa = %s WHERE usuario = %s",
                ("D.Tech - Danilo Diogo", "danilo")
            )

        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    usuario TEXT PRIMARY KEY,
                    senha TEXT,
                    db_nome TEXT,
                    empresa TEXT,
                    ativo INTEGER DEFAULT 1
                )
                """
            )

            cursor.execute("SELECT usuario FROM usuarios WHERE usuario = ?", ("danilo",))
            existe = cursor.fetchone()

            if not existe:
                cursor.execute(
                    """
                    INSERT INTO usuarios (usuario, senha, db_nome, empresa, ativo)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("danilo", "09011998Dan*", "dominio.db", "D.Tech - Danilo Diogo", 1),
                )

            cursor.execute(
                "UPDATE usuarios SET empresa = ? WHERE usuario = ?",
                ("D.Tech - Danilo Diogo", "danilo")
            )

        conn.commit()

    finally:
        cursor.close()


# ----------------------------
# LOGIN
# ----------------------------
def checar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if st.session_state["autenticado"]:
        return True

    st.markdown(
        """
        <style>
        .block-container{
            padding-top: 0.4rem !important;
        }

        [data-testid="stVerticalBlock"]{
            gap: 0.35rem !important;
        }

        .login-wrap{
            max-width: 520px;
            margin: 0 auto;
        }

        .login-title{
            margin: 0 !important;
            padding: 0 !important;
            font-size: 2.0rem;
            font-weight: 800;
        }

        .login-sub{
            margin-top: 0.3rem !important;
            opacity: .78;
        }

        div[data-testid="stForm"]{
            margin-top: 0.2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    db_url = os.getenv("DATABASE_URL", "").strip()
    usando_postgres = bool(db_url)

    conn = conectar_admin()
    preparar_admin(conn, usando_postgres, db_url)

    cursor = conn.cursor()

    try:
        col_espaco1, col_login, col_espaco2 = st.columns([1, 2, 1])

        with col_login:
            st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)

            try:
                st.image("logo.png", use_container_width=True)
            except Exception:
                pass

            st.markdown(
                """
                <div style='text-align:left; color:#00D1FF; margin-top:-12px; font-weight:400; font-size:16px;'>
                    Tecnologia que simplifica
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            st.markdown("<div class='login-title'>Acesso Seguro</div>", unsafe_allow_html=True)
            st.markdown(
                "<div class='login-sub'>Bem-vindo ao sistema <b>Gestão e Controle Financeiro</b>.</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

            st.session_state.setdefault("login_user_candidate", "")
            st.session_state.setdefault("mostrar_criar_senha", False)

            with st.form("form_login_principal", clear_on_submit=False):
                usuario_input = st.text_input(
                    "Digite seu Usuário",
                    value=st.session_state.get("login_user_candidate", "")
                ).lower().strip()

                senha_input = ""
                if not st.session_state.get("mostrar_criar_senha", False):
                    senha_input = st.text_input("Digite sua Senha", type="password")

                submit_login = st.form_submit_button(
                    "Entrar",
                    type="primary",
                    use_container_width=True
                )

            if submit_login:
                st.session_state["login_user_candidate"] = usuario_input

                if not usuario_input:
                    st.error("⚠️ Digite seu usuário.")
                    return False

                if usando_postgres:
                    cursor.execute(
                        "SELECT senha, db_nome, empresa, ativo FROM usuarios WHERE usuario=%s",
                        (usuario_input,)
                    )
                else:
                    cursor.execute(
                        "SELECT senha, db_nome, empresa, ativo FROM usuarios WHERE usuario=?",
                        (usuario_input,)
                    )

                resultado = cursor.fetchone()

                if not resultado:
                    st.warning("⚠️ Usuário não encontrado.")
                    st.session_state["mostrar_criar_senha"] = False
                    return False

                senha_bd, db_nome, empresa, ativo = resultado

                if int(ativo) == 0:
                    st.error("🚫 Acesso suspenso. Entre em contato com o suporte.")
                    st.session_state["mostrar_criar_senha"] = False
                    return False

                # --- AQUI ESTÁ A CORREÇÃO ---
                texto_senha = str(senha_bd).strip().lower()
                senha_vazia = (
                    senha_bd is None or 
                    texto_senha == "" or 
                    "pendente" in texto_senha
                )
                # ----------------------------

                if senha_vazia:
                    st.session_state["mostrar_criar_senha"] = True
                    st.session_state["empresa_tmp"] = empresa

                    if usando_postgres:
                        st.session_state["db_tmp"] = db_url
                    else:
                        st.session_state["db_tmp"] = db_nome

                    st.rerun()

                if senha_input != str(senha_bd):
                    st.error("❌ Senha incorreta.")
                    return False

                st.session_state["autenticado"] = True

                if usando_postgres:
                    st.session_state["db_nome"] = db_url
                else:
                    st.session_state["db_nome"] = db_nome

                st.session_state["empresa"] = empresa
                st.session_state["usuario_atual"] = usuario_input

                inicializar_banco(st.session_state["db_nome"])
                st.rerun()

            if st.session_state.get("mostrar_criar_senha", False):
                empresa = st.session_state.get("empresa_tmp", "")
                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                st.info(f"👋 Olá, equipe da **{empresa}**! Defina sua senha de acesso.")

                with st.form("form_nova_senha", clear_on_submit=False):
                    nova_senha = st.text_input("Crie sua Senha", type="password")
                    confirma_senha = st.text_input("Confirme sua Senha", type="password")
                    submit_senha = st.form_submit_button(
                        "Salvar e Entrar",
                        type="primary",
                        use_container_width=True
                    )

                if submit_senha:
                    u = (st.session_state.get("login_user_candidate") or "").strip()

                    if not u:
                        st.error("⚠️ Usuário inválido. Digite o usuário novamente.")
                        st.session_state["mostrar_criar_senha"] = False
                        return False

                    if not nova_senha or not confirma_senha:
                        st.error("⚠️ Preencha os dois campos de senha.")
                        return False

                    if nova_senha != confirma_senha:
                        st.error("⚠️ As senhas não conferem.")
                        return False

                    if usando_postgres:
                        cursor.execute(
                            "UPDATE usuarios SET senha=%s WHERE usuario=%s",
                            (nova_senha.strip(), u)
                        )
                    else:
                        cursor.execute(
                            "UPDATE usuarios SET senha=? WHERE usuario=?",
                            (nova_senha.strip(), u)
                        )

                    conn.commit()

                    # autentica direto após criar senha
                    st.session_state["autenticado"] = True
                    st.session_state["senha_recem_criada"] = True
                    st.session_state["mostrar_criar_senha"] = False
                    st.session_state["usuario_atual"] = u
                    st.session_state["empresa"] = st.session_state.get("empresa_tmp", "")

                    if usando_postgres:
                        st.session_state["db_nome"] = db_url
                    else:
                        st.session_state["db_nome"] = st.session_state.get("db_tmp", "")

                    inicializar_banco(st.session_state["db_nome"])
                    st.success("✅ Senha criada com sucesso!")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        return False

    finally:
        try:
            cursor.close()
        except Exception:
            pass

        try:
            conn.close()
        except Exception:
            pass
