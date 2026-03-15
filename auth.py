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
# Força usuário para primeiro acesso
# ----------------------------
def liberar_primeiro_acesso(conn, cursor, usando_postgres, usuario):
    if usando_postgres:
        cursor.execute(
            "SELECT db_nome, empresa, ativo FROM usuarios WHERE usuario=%s",
            (usuario,)
        )
    else:
        cursor.execute(
            "SELECT db_nome, empresa, ativo FROM usuarios WHERE usuario=?",
            (usuario,)
        )

    resultado = cursor.fetchone()

    if not resultado:
        return False, "⚠️ Usuário não encontrado.", None, None

    db_nome, empresa, ativo = resultado

    if int(ativo) == 0:
        return False, "🚫 Usuário bloqueado/inativo.", None, None

    if usando_postgres:
        cursor.execute(
            "UPDATE usuarios SET senha=%s WHERE usuario=%s",
            (None, usuario)
        )
        db_ref = os.getenv("DATABASE_URL", "").strip()
    else:
        cursor.execute(
            "UPDATE usuarios SET senha=? WHERE usuario=?",
            ("", usuario)
        )
        db_ref = db_nome

    conn.commit()
    return True, "", empresa, db_ref


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

                c1, c2 = st.columns(2)
                with c1:
                    submit_login = st.form_submit_button(
                        "Entrar",
                        type="primary",
                        use_container_width=True
                    )
                with c2:
                    submit_primeiro = st.form_submit_button(
                        "Primeiro acesso",
                        use_container_width=True
                    )

            if submit_primeiro:
                st.session_state["login_user_candidate"] = usuario_input

                if not usuario_input:
                    st.error("⚠️ Digite seu usuário para liberar o primeiro acesso.")
                    return False

                ok, msg, empresa, db_ref = liberar_primeiro_acesso(
                    conn, cursor, usando_postgres, usuario_input
                )

                if not ok:
                    st.error(msg)
                    st.session_state["mostrar_criar_senha"] = False
                    return False

                st.session_state["mostrar_criar_senha"] = True
                st.session_state["empresa_tmp"] = empresa
                st.session_state["db_tmp"] = db_ref
                st.success("✅ Primeiro acesso liberado. Agora crie sua senha abaixo.")
                st.rerun()

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

                senha_vazia = (
                    senha_bd is None
                    or str(senha_bd).strip() == ""
                    or str(senha_bd).strip().lower() in ["null", "none"]
                )

                if senha_vazia:
                    st.session_state["mostrar_criar_senha"] = True
                    st.session_state["empresa_tmp"] = empresa
                    st.session_state["db_tmp"] = db_url if usando_postgres else db_nome
                    st.info("👋 Primeiro acesso detectado. Crie sua senha abaixo.")
                    st.rerun()

                if senha_input != str(senha_bd):
                    st.error("❌ Senha incorreta.")
                    return False

                st.session_state["autenticado"] = True
                st.session_state["db_nome"] = db_url if usando_postgres else db_nome
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

                    st.session_state["autenticado"] = True
                    st.session_state["senha_recem_criada"] = True
                    st.session_state["mostrar_criar_senha"] = False
                    st.session_state["usuario_atual"] = u
                    st.session_state["empresa"] = st.session_state.get("empresa_tmp", "")
                    st.session_state["db_nome"] = db_url if usando_postgres else st.session_state.get("db_tmp", "")

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
