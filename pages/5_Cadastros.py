import streamlit as st
import sqlite3
import pandas as pd

from style import carregar_estilos
from auth import exigir_login
from database import conectar_banco

st.set_page_config(page_title="Cadastros", page_icon="📋", layout="wide")

try:
    st.logo("logo.png")
except:
    pass

carregar_estilos()

st.markdown("""
<style>
table { width: 100%; border-collapse: collapse; }
th, td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.08); vertical-align: middle; }
th { text-align: left; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

exigir_login()

st.title("Cadastros")
st.markdown("<span style='color: #A0AEC0;'>Gerencie contas bancárias/caixa e categorias de receitas e despesas.</span>", unsafe_allow_html=True)

# ==========================================
# BANCO DE DADOS HÍBRIDO (SQLite/Postgres)
# ==========================================
def conectar():
    db_nome = st.session_state.get("db_nome", "financas.db")
    conn, engine = conectar_banco(db_nome)
    return conn, engine

def executar_sql(conn, engine, query, params=()):
    if engine == "postgres" and params:
        query = query.replace("?", "%s")
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    try: return cur.lastrowid
    except: return 0

tab1, tab2 = st.tabs(["Contas (Bancos/Caixa)", "Categorias"])

# -------------------------
# CONTAS
# -------------------------
with tab1:
    col_form, col_table = st.columns([1, 1.7])

    with col_form:
        st.subheader("Nova conta")
        with st.form("form_conta", clear_on_submit=True):
            nome_conta = st.text_input("Nome da conta", placeholder="Ex: Itaú Empresa, Caixa Físico, Cora")
            tipo_conta = st.selectbox("Tipo", ["Conta Corrente", "Caixa (Dinheiro)", "Cartão de Crédito", "Poupança/Investimento"], key="tipo_conta_select")
            submit_conta = st.form_submit_button("Salvar", use_container_width=True)

            if submit_conta:
                if nome_conta.strip():
                    conn, engine = conectar()
                    executar_sql(conn, engine, "INSERT INTO accounts (nome, tipo) VALUES (?, ?)", (nome_conta.strip(), tipo_conta))
                    conn.close()
                    st.success("Conta cadastrada com sucesso.")
                    st.rerun()
                else:
                    st.warning("O nome da conta é obrigatório.")

        st.divider()
        st.subheader("Ação rápida")

        conn, engine = conectar()
        df_contas_raw = pd.read_sql_query("SELECT id, nome, tipo FROM accounts ORDER BY id DESC", conn)
        conn.close()

        if df_contas_raw.empty:
            st.info("Nenhuma conta cadastrada ainda.")
        else:
            op = df_contas_raw.apply(lambda r: f"ID {r['id']} | {r['nome']} ({r['tipo']})", axis=1).tolist()
            map_id = dict(zip(op, df_contas_raw["id"].tolist()))

            escolha = st.selectbox("Selecionar conta", options=op, key="select_conta_acao")
            id_sel = int(map_id[escolha])

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Preparar exclusão", key="btn_preparar_excluir_conta", use_container_width=True):
                    st.session_state["conf_excluir_conta"] = id_sel

            with c2:
                if st.session_state.get("conf_excluir_conta") == id_sel:
                    if st.button("Confirmar exclusão", key="btn_confirmar_excluir_conta", type="primary", use_container_width=True):
                        conn, engine = conectar()
                        try:
                            executar_sql(conn, engine, "DELETE FROM accounts WHERE id=?", (id_sel,))
                            st.success("Conta excluída.")
                        except Exception as e:
                            st.error("Não foi possível excluir. Talvez existam lançamentos vinculados a esta conta.")
                        finally:
                            conn.close()

                        st.session_state.pop("conf_excluir_conta", None)
                        st.rerun()

    with col_table:
        st.subheader("Contas cadastradas")
        busca = st.text_input("Buscar conta", placeholder="Digite para filtrar...", key="busca_conta")

        conn, engine = conectar()
        df_contas = pd.read_sql_query("SELECT id as ID, nome as Nome, tipo as Tipo FROM accounts ORDER BY id DESC", conn)
        conn.close()

        if busca.strip():
            df_contas = df_contas[df_contas["Nome"].astype(str).str.contains(busca.strip(), case=False, na=False)]

        if df_contas.empty:
            st.info("Nenhuma conta encontrada.")
        else:
            e1, e2 = st.columns(2)
            with e1:
                st.download_button("Baixar CSV", data=df_contas.to_csv(index=False, sep=";").encode("utf-8"), file_name="contas.csv", mime="text/csv", use_container_width=True, key="down_contas_csv")
            with e2:
                try:
                    import io
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                        df_contas.to_excel(writer, index=False, sheet_name="Contas")
                    st.download_button("Baixar Excel", data=buf.getvalue(), file_name="contas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="down_contas_xlsx")
                except:
                    st.warning("Para baixar Excel: pip install openpyxl")

            st.dataframe(df_contas, hide_index=True, use_container_width=True)

# -------------------------
# CATEGORIAS
# -------------------------
with tab2:
    col_form_cat, col_table_cat = st.columns([1, 1.7])

    with col_form_cat:
        st.subheader("Nova categoria")
        with st.form("form_categoria", clear_on_submit=True):
            nome_categoria = st.text_input("Nome da categoria", placeholder="Ex: Vendas, Fornecedores, Impostos")
            tipo_categoria = st.selectbox("Tipo", ["Entrada", "Saída"], key="tipo_categoria_select")
            submit_categoria = st.form_submit_button("Salvar", use_container_width=True)

            if submit_categoria:
                if nome_categoria.strip():
                    conn, engine = conectar()
                    executar_sql(conn, engine, "INSERT INTO categories (nome, tipo) VALUES (?, ?)", (nome_categoria.strip(), tipo_categoria))
                    conn.close()
                    st.success("Categoria cadastrada com sucesso.")
                    st.rerun()
                else:
                    st.warning("O nome da categoria é obrigatório.")

        st.divider()
        st.subheader("Ação rápida")

        conn, engine = conectar()
        df_cat_raw = pd.read_sql_query("SELECT id, nome, tipo FROM categories ORDER BY id DESC", conn)
        conn.close()

        if df_cat_raw.empty:
            st.info("Nenhuma categoria cadastrada ainda.")
        else:
            op = df_cat_raw.apply(lambda r: f"ID {r['id']} | {r['nome']} ({r['tipo']})", axis=1).tolist()
            map_id = dict(zip(op, df_cat_raw["id"].tolist()))

            escolha = st.selectbox("Selecionar categoria", options=op, key="select_cat_acao")
            id_sel = int(map_id[escolha])

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Preparar exclusão", key="btn_preparar_excluir_cat", use_container_width=True):
                    st.session_state["conf_excluir_cat"] = id_sel

            with c2:
                if st.session_state.get("conf_excluir_cat") == id_sel:
                    if st.button("Confirmar exclusão", key="btn_confirmar_excluir_cat", type="primary", use_container_width=True):
                        conn, engine = conectar()
                        try:
                            executar_sql(conn, engine, "DELETE FROM categories WHERE id=?", (id_sel,))
                            st.success("Categoria excluída.")
                        except Exception as e:
                            st.error("Não foi possível excluir. Talvez existam lançamentos vinculados a esta categoria.")
                        finally:
                            conn.close()

                        st.session_state.pop("conf_excluir_cat", None)
                        st.rerun()

    with col_table_cat:
        st.subheader("Categorias cadastradas")
        busca = st.text_input("Buscar categoria", placeholder="Digite para filtrar...", key="busca_cat")

        conn, engine = conectar()
        df_categorias = pd.read_sql_query("SELECT id as ID, nome as Nome, tipo as Tipo FROM categories ORDER BY id DESC", conn)
        conn.close()

        if busca.strip():
            df_categorias = df_categorias[df_categorias["Nome"].astype(str).str.contains(busca.strip(), case=False, na=False)]

        if df_categorias.empty:
            st.info("Nenhuma categoria encontrada.")
        else:
            e1, e2 = st.columns(2)
            with e1:
                st.download_button("Baixar CSV", data=df_categorias.to_csv(index=False, sep=";").encode("utf-8"), file_name="categorias.csv", mime="text/csv", use_container_width=True, key="down_cat_csv")
            with e2:
                try:
                    import io
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                        df_categorias.to_excel(writer, index=False, sheet_name="Categorias")
                    st.download_button("Baixar Excel", data=buf.getvalue(), file_name="categorias.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="down_cat_xlsx")
                except:
                    st.warning("Para baixar Excel: pip install openpyxl")

            st.dataframe(df_categorias, hide_index=True, use_container_width=True)
