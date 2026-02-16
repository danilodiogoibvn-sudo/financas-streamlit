import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Cadastros", page_icon="📋", layout="wide")
st.logo("logo.png")

# ============================
# UI COMPACTA (SIDEBAR MENOR + CONTEÚDO MAIOR)
# Cole em TODAS as telas (logo após st.set_page_config)
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

/* 3) Ajusta padding do conteúdo (tira espaço “sobrando” dos lados) */
.block-container{
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    padding-top: 1.2rem !important;
}

/* 4) Opcional: deixa o menu lateral mais “enxuto” */
[data-testid="stSidebarNav"] li a{
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}

/* 5) Opcional: reduz um pouco o espaçamento dos headers */
h1, h2, h3 { margin-bottom: 0.2rem !important; }
</style>
""", unsafe_allow_html=True)

from auth import exigir_login
exigir_login()


st.title("Cadastros")
st.markdown("Gerencie contas bancárias/caixa e categorias de receitas e despesas.")

def conectar():
    return sqlite3.connect(st.session_state["db_nome"])

# CSS leve (opcional)
st.markdown("""
<style>
table { width: 100%; border-collapse: collapse; }
th, td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.08); vertical-align: middle; }
th { text-align: left; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

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
            tipo_conta = st.selectbox(
                "Tipo",
                ["Conta Corrente", "Caixa (Dinheiro)", "Cartão de Crédito", "Poupança/Investimento"],
                key="tipo_conta_select"
            )
            submit_conta = st.form_submit_button("Salvar", use_container_width=True)

            if submit_conta:
                if nome_conta.strip():
                    conn = conectar()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO accounts (nome, tipo) VALUES (?, ?)", (nome_conta.strip(), tipo_conta))
                    conn.commit()
                    conn.close()
                    st.success("Conta cadastrada com sucesso.")
                    st.rerun()
                else:
                    st.warning("O nome da conta é obrigatório.")

        st.divider()
        st.subheader("Ação rápida")

        conn = conectar()
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
                        conn = conectar()
                        cur = conn.cursor()
                        try:
                            cur.execute("DELETE FROM accounts WHERE id=?", (id_sel,))
                            conn.commit()
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

        conn = conectar()
        df_contas = pd.read_sql_query("SELECT id as ID, nome as Nome, tipo as Tipo FROM accounts ORDER BY id DESC", conn)
        conn.close()

        if busca.strip():
            df_contas = df_contas[df_contas["Nome"].astype(str).str.contains(busca.strip(), case=False, na=False)]

        if df_contas.empty:
            st.info("Nenhuma conta encontrada.")
        else:
            e1, e2 = st.columns(2)
            with e1:
                st.download_button(
                    "Baixar CSV",
                    data=df_contas.to_csv(index=False, sep=";").encode("utf-8"),
                    file_name="contas.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="down_contas_csv"
                )
            with e2:
                try:
                    import io
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                        df_contas.to_excel(writer, index=False, sheet_name="Contas")
                    st.download_button(
                        "Baixar Excel",
                        data=buf.getvalue(),
                        file_name="contas.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="down_contas_xlsx"
                    )
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
                    conn = conectar()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO categories (nome, tipo) VALUES (?, ?)", (nome_categoria.strip(), tipo_categoria))
                    conn.commit()
                    conn.close()
                    st.success("Categoria cadastrada com sucesso.")
                    st.rerun()
                else:
                    st.warning("O nome da categoria é obrigatório.")

        st.divider()
        st.subheader("Ação rápida")

        conn = conectar()
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
                        conn = conectar()
                        cur = conn.cursor()
                        try:
                            cur.execute("DELETE FROM categories WHERE id=?", (id_sel,))
                            conn.commit()
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

        conn = conectar()
        df_categorias = pd.read_sql_query("SELECT id as ID, nome as Nome, tipo as Tipo FROM categories ORDER BY id DESC", conn)
        conn.close()

        if busca.strip():
            df_categorias = df_categorias[df_categorias["Nome"].astype(str).str.contains(busca.strip(), case=False, na=False)]

        if df_categorias.empty:
            st.info("Nenhuma categoria encontrada.")
        else:
            e1, e2 = st.columns(2)
            with e1:
                st.download_button(
                    "Baixar CSV",
                    data=df_categorias.to_csv(index=False, sep=";").encode("utf-8"),
                    file_name="categorias.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="down_cat_csv"
                )
            with e2:
                try:
                    import io
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                        df_categorias.to_excel(writer, index=False, sheet_name="Categorias")
                    st.download_button(
                        "Baixar Excel",
                        data=buf.getvalue(),
                        file_name="categorias.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="down_cat_xlsx"
                    )
                except:
                    st.warning("Para baixar Excel: pip install openpyxl")

            st.dataframe(df_categorias, hide_index=True, use_container_width=True)
