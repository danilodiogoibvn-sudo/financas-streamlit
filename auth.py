import streamlit as st
import sqlite3
import os
from database import inicializar_banco

# ----------------------------
# LOGOUT (para usar nas páginas)
# ----------------------------
def fazer_logout():
    # Limpa apenas o que a gente usa no login (não destrói tudo do app)
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
    Use nas OUTRAS páginas:
    - Não mostra tela de login
    - Se não estiver logado, trava/manda pra Home
    """
    if st.session_state.get("autenticado"):
        return

    st.warning("Você precisa fazer login na Home para acessar esta página.")
    # Se você quiser redirecionar de verdade depois, dá pra usar st.switch_page aqui.
    st.stop()


# Conexão com o cofre de usuários (admin)
def conectar_admin():
    db_url = os.getenv("DATABASE_URL", "").strip()
    is_postgres = bool(db_url)

    if is_postgres:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Cria a tabela se não existir (Postgres)
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

        # Garante que o Danilo existe
        cursor.execute("SELECT usuario FROM usuarios WHERE usuario=%s", ("danilo",))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, db_nome, empresa, ativo) VALUES (%s, %s, %s, %s, %s)",
                ("danilo", "09011998Dan*", db_url, "Domínio Ferramentas", 1),
            )
            conn.commit()

        return conn

    # Local (SQLite)
    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()

    # Cria a tabela se não existir
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

    # Garante que o Danilo existe
    cursor.execute("SELECT * FROM usuarios WHERE usuario='danilo'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO usuarios (usuario, senha, db_nome, empresa, ativo) VALUES (?, ?, ?, ?, ?)",
            ("danilo", "09011998Dan*", "dominio.db", "Domínio Ferramentas", 1),
        )
        conn.commit()

    return conn


def checar_senha():
    # Se já autenticou, libera direto (sem abrir conexão)
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if st.session_state["autenticado"]:
        return True

    # ============================
    # CSS: Login em 1 tela + mais pra cima
    # (só visual, não muda estrutura do app)
    # ============================
    st.markdown(
        """
        <style>
        /* puxa tudo pra cima */
        .block-container{
            padding-top: 0.4rem !important;
        }

        /* reduz espaços padrão */
        [data-testid="stVerticalBlock"]{
            gap: 0.35rem !important;
        }

        /* deixa o container do login mais “compacto” */
        .login-wrap{
            max-width: 520px;
            margin: 0 auto;
        }

        /* título e textos mais enxutos */
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

        /* ajusta o espaço do form */
        div[data-testid="stForm"]{
            margin-top: 0.2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    conn = conectar_admin()
    cursor = conn.cursor()

    # Detecta se está no Postgres para usar placeholders corretos
    db_url = os.getenv("DATABASE_URL", "").strip()
    usando_postgres = bool(db_url)

    try:
        col_espaco1, col_login, col_espaco2 = st.columns([1, 2, 1])

        with col_login:
            st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)

            # --- IDENTIDADE VISUAL ---
            try:
                # um pouco menor pra caber em 1 tela
                st.image("logo.png", use_container_width=True)
            except:
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

            # ----------------------------
            # Fluxo: candidato (usuário) + estado do primeiro acesso
            # ----------------------------
            st.session_state.setdefault("login_user_candidate", "")
            st.session_state.setdefault("mostrar_criar_senha", False)

            # ----------------------------
            # FORM PRINCIPAL (TAB correto + ENTER envia)
            # ----------------------------
            with st.form("form_login_principal", clear_on_submit=False):
                usuario_input = st.text_input(
                    "Digite seu Usuário",
                    value=st.session_state.get("login_user_candidate", ""),
                ).lower().strip()

                # só mostra senha quando NÃO está no fluxo de criar senha
                senha_input = ""
                if not st.session_state.get("mostrar_criar_senha", False):
                    senha_input = st.text_input("Digite sua Senha", type="password")

                submit_login = st.form_submit_button("Entrar", type="primary", use_container_width=True)

            # Se clicou/enter no "Entrar"
            if submit_login:
                st.session_state["login_user_candidate"] = usuario_input

                if not usuario_input:
                    st.error("⚠️ Digite seu usuário.")
                    return False

                if usando_postgres:
                    cursor.execute(
                        "SELECT senha, db_nome, empresa, ativo FROM usuarios WHERE usuario=%s",
                        (usuario_input,),
                    )
                else:
                    cursor.execute(
                        "SELECT senha, db_nome, empresa, ativo FROM usuarios WHERE usuario=?",
                        (usuario_input,),
                    )
                resultado = cursor.fetchone()

                if not resultado:
                    st.warning("⚠️ Usuário não encontrado.")
                    st.session_state["mostrar_criar_senha"] = False
                    return False

                senha_bd, db_nome, empresa, ativo = resultado

                # 1) BLOQUEIO
                if int(ativo) == 0:
                    st.error("🚫 Acesso suspenso. Entre em contato com o suporte.")
                    st.session_state["mostrar_criar_senha"] = False
                    return False

                # 2) PRIMEIRO ACESSO (Senha vazia no banco)
                if senha_bd == "" or senha_bd is None:
                    st.session_state["mostrar_criar_senha"] = True
                    st.session_state["empresa_tmp"] = empresa

                    # No cloud, força o db a ser o DATABASE_URL
                    if usando_postgres:
                        st.session_state["db_tmp"] = db_url
                    else:
                        st.session_state["db_tmp"] = db_nome

                    st.info(f"👋 Olá, equipe da **{empresa}**! Defina sua senha de acesso.")
                    st.rerun()

                # 3) LOGIN NORMAL
                if senha_input != senha_bd:
                    st.error("❌ Senha incorreta.")
                    return False

                # OK
                st.session_state["autenticado"] = True

                # No cloud, db_nome vira o DATABASE_URL (Neon)
                if usando_postgres:
                    st.session_state["db_nome"] = db_url
                else:
                    st.session_state["db_nome"] = db_nome

                st.session_state["empresa"] = empresa
                st.session_state["usuario_atual"] = usuario_input

                inicializar_banco(st.session_state["db_nome"])
                st.rerun()

            # ----------------------------
            # FORM: CRIAR SENHA (primeiro acesso)
            # (fica fora do form principal pra não bugar TAB/ENTER)
            # ----------------------------
            if st.session_state.get("mostrar_criar_senha", False):
                empresa = st.session_state.get("empresa_tmp", "")
                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                st.info(f"👋 Olá, equipe da **{empresa}**! Defina sua senha de acesso.")

                with st.form("form_nova_senha", clear_on_submit=False):
                    nova_senha = st.text_input("Crie sua Senha", type="password")
                    confirma_senha = st.text_input("Confirme sua Senha", type="password")
                    submit_senha = st.form_submit_button("Salvar e Entrar", type="primary", use_container_width=True)

                if submit_senha:
                    u = (st.session_state.get("login_user_candidate") or "").strip()
                    if not u:
                        st.error("⚠️ Usuário inválido. Digite o usuário novamente.")
                        st.session_state["mostrar_criar_senha"] = False
                        return False

                    if not nova_senha or nova_senha != confirma_senha:
                        st.error("⚠️ As senhas não conferem ou estão vazias.")
                        return False

                    if usando_postgres:
                        cursor.execute(
                            "UPDATE usuarios SET senha=%s WHERE usuario=%s",
                            (nova_senha, u),
                        )
                    else:
                        cursor.execute(
                            "UPDATE usuarios SET senha=? WHERE usuario=?",
                            (nova_senha, u),
                        )
                    conn.commit()

                    st.success("✅ Senha criada! Agora você já pode entrar.")
                    st.session_state["senha_recem_criada"] = True
                    st.session_state["mostrar_criar_senha"] = False
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        return False

    finally:
        conn.close()
