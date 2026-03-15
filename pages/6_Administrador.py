import streamlit as st
import sqlite3
import os
from datetime import date, timedelta

from database import inicializar_banco
from auth import exigir_login

st.set_page_config(page_title="Administração", page_icon="⚙️", layout="wide")
st.logo("logo.png")

# ============================
# UI COMPACTA (SIDEBAR MENOR + CONTEÚDO MAIOR)
# ============================
st.markdown("""
<style>
/* 1) Diminui a sidebar (menu lateral) */
[data-testid="stSidebar"]{
    width: 190px !important;
    min-width: 190px !important;
}

/* 2) Dá mais espaço pro conteúdo principal */
section.main > div{
    max-width: 100% !important;
}

/* 3) Ajusta padding do conteúdo */
.block-container{
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    padding-top: 1.2rem !important;
}

/* 4) Menu lateral mais enxuto */
[data-testid="stSidebarNav"] li a{
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}

/* 5) Headers */
h1, h2, h3 { margin-bottom: 0.2rem !important; }
</style>
""", unsafe_allow_html=True)

# 1) Segurança: Login
exigir_login()

# 2) Segurança: Só Danilo
if st.session_state.get("usuario_atual") != "danilo":
    st.error("ACESSO NEGADO: você não tem permissão para acessar o painel de administrador.")
    st.stop()

st.title("Painel do Administrador")
st.markdown(f"Bem-vindo, **{st.session_state['usuario_atual'].title()}**. Controle de clientes, planos e cobrança.")
st.divider()

col1, col2 = st.columns([1, 2])

# -----------------------------
# Helpers
# -----------------------------
def fmt_brl(x):
    try:
        return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


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
        return conn, True, db_url

    conn = sqlite3.connect("admin.db")
    return conn, False, "admin.db"


def preparar_admin(conn, usando_postgres, db_url):
    cur = conn.cursor()
    try:
        # Cria a tabela já completa para evitar ALTER TABLE no Postgres
        if usando_postgres:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    usuario TEXT PRIMARY KEY,
                    senha TEXT,
                    db_nome TEXT,
                    empresa TEXT,
                    ativo INTEGER DEFAULT 1,
                    plano TEXT DEFAULT 'Starter',
                    valor_mensal DOUBLE PRECISION DEFAULT 0,
                    vencimento TEXT
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    usuario TEXT PRIMARY KEY,
                    senha TEXT,
                    db_nome TEXT,
                    empresa TEXT,
                    ativo INTEGER DEFAULT 1,
                    plano TEXT DEFAULT 'Starter',
                    valor_mensal REAL DEFAULT 0,
                    vencimento TEXT
                )
            """)

        # Garantia extra para SQLite antigo
        if not usando_postgres:
            try:
                cur.execute("ALTER TABLE usuarios ADD COLUMN ativo INTEGER DEFAULT 1")
            except Exception:
                pass

            try:
                cur.execute("ALTER TABLE usuarios ADD COLUMN plano TEXT DEFAULT 'Starter'")
            except Exception:
                pass

            try:
                cur.execute("ALTER TABLE usuarios ADD COLUMN valor_mensal REAL DEFAULT 0")
            except Exception:
                pass

            try:
                cur.execute("ALTER TABLE usuarios ADD COLUMN vencimento TEXT")
            except Exception:
                pass

        # Garante usuário principal
        if usando_postgres:
            cur.execute("SELECT usuario FROM usuarios WHERE usuario=%s", ("danilo",))
            existe = cur.fetchone()

            if not existe:
                cur.execute("""
                    INSERT INTO usuarios (
                        usuario, senha, db_nome, empresa, ativo, plano, valor_mensal, vencimento
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    "danilo",
                    "09011998Dan*",
                    db_url,
                    "D.Tech - Danilo Diogo",
                    1,
                    "Business",
                    0,
                    None
                ))
            else:
                cur.execute(
                    "UPDATE usuarios SET empresa=%s WHERE usuario=%s",
                    ("D.Tech - Danilo Diogo", "danilo")
                )

        else:
            cur.execute("SELECT usuario FROM usuarios WHERE usuario=?", ("danilo",))
            existe = cur.fetchone()

            if not existe:
                cur.execute("""
                    INSERT INTO usuarios (
                        usuario, senha, db_nome, empresa, ativo, plano, valor_mensal, vencimento
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "danilo",
                    "09011998Dan*",
                    "dominio.db",
                    "D.Tech - Danilo Diogo",
                    1,
                    "Business",
                    0,
                    None
                ))
            else:
                cur.execute(
                    "UPDATE usuarios SET empresa=? WHERE usuario=?",
                    ("D.Tech - Danilo Diogo", "danilo")
                )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()


PLANOS = {
    "Starter": 49.90,
    "Pro": 99.90,
    "Business": 199.90,
}

# ==================================================
# COLUNA ESQUERDA: NOVO CLIENTE
# ==================================================
with col1:
    st.subheader("Novo Cliente")

    with st.container(border=True):
        st.info("Cadastre usuário e empresa. A senha será criada pelo cliente no primeiro acesso.")

        with st.form("form_novo_cliente", clear_on_submit=True):
            novo_user = st.text_input("Login do Cliente (sem espaços)").strip().lower()
            nova_empresa = st.text_input("Nome da Empresa").strip()

            st.divider()
            st.caption("Configuração SaaS")

            plano_sel = st.selectbox("Plano", options=list(PLANOS.keys()), index=0)
            valor_sugerido = float(PLANOS.get(plano_sel, 0))

            valor_mensal = st.number_input(
                "Valor mensal (R$)",
                min_value=0.0,
                step=10.0,
                value=valor_sugerido,
                format="%.2f"
            )

            vencimento = st.date_input(
                "Vencimento da próxima fatura",
                value=(date.today() + timedelta(days=30))
            )

            submit = st.form_submit_button("Gerar Acesso", type="primary", use_container_width=True)

            if submit:
                if not novo_user or not nova_empresa:
                    st.warning("Preencha todos os campos.")
                elif " " in novo_user:
                    st.warning("O login não pode conter espaços.")
                else:
                    conn, usando_postgres, db_ref = conectar_admin()
                    try:
                        preparar_admin(conn, usando_postgres, db_ref)
                        cur = conn.cursor()

                        novo_db = f"cliente_{novo_user}.db"

                        if usando_postgres:
                            cur.execute("SELECT usuario FROM usuarios WHERE usuario=%s", (novo_user,))
                            existe = cur.fetchone()

                            if existe:
                                st.error("Erro: este usuário já existe.")
                            else:
                                cur.execute("""
                                    INSERT INTO usuarios (
                                        usuario, senha, db_nome, empresa, ativo, plano, valor_mensal, vencimento
                                    )
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    novo_user,
                                    None,  # primeiro acesso no Neon/Postgres
                                    novo_db,
                                    nova_empresa,
                                    1,
                                    plano_sel,
                                    float(valor_mensal),
                                    vencimento.isoformat()
                                ))
                                conn.commit()

                                # No cloud, tudo usa o mesmo Postgres
                                inicializar_banco(db_ref)

                                st.success(f"Cliente **{novo_user}** criado com sucesso!")
                                st.balloons()

                        else:
                            cur.execute("SELECT usuario FROM usuarios WHERE usuario=?", (novo_user,))
                            existe = cur.fetchone()

                            if existe:
                                st.error("Erro: este usuário já existe.")
                            else:
                                cur.execute("""
                                    INSERT INTO usuarios (
                                        usuario, senha, db_nome, empresa, ativo, plano, valor_mensal, vencimento
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    novo_user,
                                    "",  # primeiro acesso no SQLite
                                    novo_db,
                                    nova_empresa,
                                    1,
                                    plano_sel,
                                    float(valor_mensal),
                                    vencimento.isoformat()
                                ))
                                conn.commit()

                                # No local, cria o banco do cliente
                                inicializar_banco(novo_db)

                                st.success(f"Cliente **{novo_user}** criado com sucesso!")
                                st.balloons()

                        cur.close()

                    except Exception as e:
                        st.error(f"Falha ao criar cliente: {e}")
                    finally:
                        conn.close()

# ==================================================
# COLUNA DIREITA: LISTA / GESTÃO
# ==================================================
with col2:
    st.subheader("Gestão de Clientes")

    f1, f2, f3 = st.columns([2.2, 1.1, 1.1])
    with f1:
        busca = st.text_input("Buscar por empresa ou login", placeholder="Digite para filtrar...")
    with f2:
        mostrar_bloqueados = st.checkbox("Mostrar bloqueados", value=True)
    with f3:
        somente_vencidos = st.checkbox("Somente vencidos", value=False)

    conn, usando_postgres, db_ref = conectar_admin()
    try:
        preparar_admin(conn, usando_postgres, db_ref)
        cur = conn.cursor()

        if usando_postgres:
            cur.execute("""
                SELECT usuario, empresa, db_nome, ativo, senha, plano, valor_mensal, vencimento
                FROM usuarios
                WHERE usuario != %s
                ORDER BY empresa ASC
            """, ("danilo",))
        else:
            cur.execute("""
                SELECT usuario, empresa, db_nome, ativo, senha, plano, valor_mensal, vencimento
                FROM usuarios
                WHERE usuario != ?
                ORDER BY empresa COLLATE NOCASE ASC
            """, ("danilo",))

        clientes = cur.fetchall()

        if not clientes:
            st.info("Nenhum cliente cadastrado além de você.")
        else:
            hoje = date.today()
            clientes_filtrados = []

            for cli in clientes:
                user, emp, db, ativo, senha_atual, plano, valor_mensal, venc = cli
                ativo = int(ativo) if ativo is not None else 1
                plano = plano or "Starter"
                valor_mensal = float(valor_mensal or 0)

                venc_dt = None
                if venc:
                    try:
                        venc_dt = date.fromisoformat(str(venc))
                    except Exception:
                        venc_dt = None

                if not mostrar_bloqueados and ativo == 0:
                    continue

                if busca.strip():
                    b = busca.strip().lower()
                    if b not in str(user).lower() and b not in str(emp).lower():
                        continue

                if somente_vencidos:
                    if venc_dt is None:
                        continue
                    if venc_dt >= hoje:
                        continue

                clientes_filtrados.append((user, emp, db, ativo, senha_atual, plano, valor_mensal, venc_dt))

            if not clientes_filtrados:
                st.info("Nenhum cliente encontrado com os filtros.")
            else:
                for (user, emp, db, ativo, senha_atual, plano, valor_mensal, venc_dt) in clientes_filtrados:
                    status_texto = "ATIVO" if ativo == 1 else "BLOQUEADO"
                    senha_texto = "Pendente (primeiro acesso)" if (senha_atual is None or str(senha_atual).strip() == "") else "Definida"

                    if venc_dt is None:
                        venc_str = "Não definido"
                        situacao = "SEM VENCIMENTO"
                        situacao_cor = "warning"
                    else:
                        venc_str = venc_dt.strftime("%d/%m/%Y")
                        if venc_dt < date.today():
                            situacao = "VENCIDO"
                            situacao_cor = "error"
                        else:
                            situacao = "EM DIA"
                            situacao_cor = "success"

                    with st.container(border=True):
                        topo1, topo2 = st.columns([3, 1])

                        with topo1:
                            st.markdown(f"### {emp}")
                            st.caption(f"Login: `{user}`  |  Banco: `{db}`")
                            st.caption(f"Senha: **{senha_texto}**")

                        with topo2:
                            if ativo == 1:
                                st.success(status_texto)
                            else:
                                st.error(status_texto)

                        st.divider()

                        sa1, sa2, sa3, sa4 = st.columns([1.2, 1.2, 1.2, 1.4])
                        with sa1:
                            st.caption("Plano")
                            st.write(f"**{plano}**")
                        with sa2:
                            st.caption("Valor mensal")
                            st.write(f"**{fmt_brl(valor_mensal)}**")
                        with sa3:
                            st.caption("Vencimento")
                            st.write(f"**{venc_str}**")
                        with sa4:
                            st.caption("Situação")
                            if situacao_cor == "success":
                                st.success(situacao)
                            elif situacao_cor == "error":
                                st.error(situacao)
                            else:
                                st.warning(situacao)

                        st.divider()

                        b1, b2, b3, b4 = st.columns(4)

                        # 1) Bloquear / Ativar
                        with b1:
                            novo_status = 0 if ativo == 1 else 1
                            label = "Bloquear" if ativo == 1 else "Ativar"
                            if st.button(label, key=f"block_{user}", use_container_width=True):
                                try:
                                    c1 = conn.cursor()
                                    if usando_postgres:
                                        c1.execute("UPDATE usuarios SET ativo=%s WHERE usuario=%s", (novo_status, user))
                                    else:
                                        c1.execute("UPDATE usuarios SET ativo=? WHERE usuario=?", (novo_status, user))
                                    conn.commit()
                                    c1.close()
                                    st.rerun()
                                except Exception as e:
                                    conn.rollback()
                                    st.error(f"Erro ao alterar status: {e}")

                        # 2) Liberar primeiro acesso / resetar senha
                        with b2:
                            if st.button("Liberar 1º acesso", key=f"reset_{user}", use_container_width=True):
                                try:
                                    c2 = conn.cursor()
                                    if usando_postgres:
                                        c2.execute("UPDATE usuarios SET senha=%s WHERE usuario=%s", (None, user))
                                    else:
                                        c2.execute("UPDATE usuarios SET senha=? WHERE usuario=?", ("", user))
                                    conn.commit()
                                    c2.close()
                                    st.success(f"Primeiro acesso liberado para {user}.")
                                    st.rerun()
                                except Exception as e:
                                    conn.rollback()
                                    st.error(f"Erro ao liberar primeiro acesso: {e}")

                        # 3) Editar plano
                        with b3:
                            if st.button("Editar plano", key=f"edit_{user}", use_container_width=True):
                                st.session_state[f"edit_open_{user}"] = True

                        # 4) Excluir
                        with b4:
                            conf_key = f"conf_del_{user}"
                            if conf_key not in st.session_state:
                                st.session_state[conf_key] = False

                            if not st.session_state[conf_key]:
                                if st.button("Excluir", key=f"prep_del_{user}", type="primary", use_container_width=True):
                                    st.session_state[conf_key] = True
                                    st.rerun()
                            else:
                                st.warning("Confirme para excluir.")
                                if st.button("Confirmar", key=f"confirm_del_{user}", type="primary", use_container_width=True):
                                    try:
                                        c4 = conn.cursor()
                                        if usando_postgres:
                                            c4.execute("DELETE FROM usuarios WHERE usuario=%s", (user,))
                                        else:
                                            c4.execute("DELETE FROM usuarios WHERE usuario=?", (user,))
                                        conn.commit()
                                        c4.close()
                                        st.session_state[conf_key] = False
                                        st.error(f"Cliente {user} removido permanentemente.")
                                        st.rerun()
                                    except Exception as e:
                                        conn.rollback()
                                        st.error(f"Erro ao excluir cliente: {e}")

                        # painel de edição
                        if st.session_state.get(f"edit_open_{user}", False):
                            st.divider()
                            st.subheader("Editar plano / cobrança")

                            with st.form(f"form_edit_{user}"):
                                novo_plano = st.selectbox(
                                    "Plano",
                                    options=list(PLANOS.keys()),
                                    index=list(PLANOS.keys()).index(plano) if plano in PLANOS else 0,
                                    key=f"plano_{user}"
                                )

                                novo_valor = st.number_input(
                                    "Valor mensal (R$)",
                                    min_value=0.0,
                                    step=10.0,
                                    value=float(valor_mensal),
                                    format="%.2f",
                                    key=f"valor_{user}"
                                )

                                venc_padrao = venc_dt if venc_dt else (date.today() + timedelta(days=30))
                                novo_venc = st.date_input(
                                    "Vencimento",
                                    value=venc_padrao,
                                    key=f"venc_{user}"
                                )

                                csave, ccancel = st.columns([1, 1])
                                with csave:
                                    salvar = st.form_submit_button("Salvar", type="primary", use_container_width=True)
                                with ccancel:
                                    cancelar = st.form_submit_button("Cancelar", use_container_width=True)

                                if salvar:
                                    try:
                                        c3 = conn.cursor()
                                        if usando_postgres:
                                            c3.execute("""
                                                UPDATE usuarios
                                                SET plano=%s, valor_mensal=%s, vencimento=%s
                                                WHERE usuario=%s
                                            """, (novo_plano, float(novo_valor), novo_venc.isoformat(), user))
                                        else:
                                            c3.execute("""
                                                UPDATE usuarios
                                                SET plano=?, valor_mensal=?, vencimento=?
                                                WHERE usuario=?
                                            """, (novo_plano, float(novo_valor), novo_venc.isoformat(), user))
                                        conn.commit()
                                        c3.close()
                                        st.session_state[f"edit_open_{user}"] = False
                                        st.success("Dados atualizados.")
                                        st.rerun()
                                    except Exception as e:
                                        conn.rollback()
                                        st.error(f"Erro ao atualizar dados: {e}")

                                if cancelar:
                                    st.session_state[f"edit_open_{user}"] = False
                                    st.rerun()

        cur.close()

    finally:
        conn.close()