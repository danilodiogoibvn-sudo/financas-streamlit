import streamlit as st
import pandas as pd
from datetime import date, datetime
import re
import calendar

# --- 🚀 OS DOIS IMPORTS NOVOS PARA O IPHONE ---
import base64
import streamlit.components.v1 as components

# --- IMPORTANDO SEUS MÓDULOS D.TECH ---
from style import carregar_estilos
from components import metric_card, icon_svg
from auth import exigir_login
from database import conectar_banco

# ==========================================
# 1) CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Sistema Financeiro | D.Tech", # Troque o título dependendo da página
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2) TRUQUE MÁGICO DO IPHONE (Apple Touch Icon)
# ==========================================
try:
    with open("logo.png", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
        
    components.html(
        f"""
        <script>
            var link = window.parent.document.createElement('link');
            link.rel = 'apple-touch-icon';
            link.href = 'data:image/png;base64,{img_b64}';
            window.parent.document.head.appendChild(link);
        </script>
        """,
        height=0, width=0
    )
except:
    pass

# ==========================================
# 3) LOGO DO MENU LATERAL
# ==========================================
try:
    st.logo("logo.png")
except:
    pass

carregar_estilos()

st.markdown("""
<style>
/* ===== TABELA SaaS D.TECH ===== */
table { width:100%; border-collapse:separate; border-spacing:0; }
thead th {
    text-align:center !important;
    font-weight:800;
    letter-spacing:0.5px;
    padding:12px 12px;
    border-bottom:1px solid rgba(0, 209, 255, 0.3);
    background:rgba(0, 209, 255, 0.05);
    color: #00D1FF;
}
tbody td {
    padding:12px 12px;
    border-bottom:1px solid rgba(255,255,255,0.05);
    vertical-align:middle;
}
tbody tr:hover td { background:rgba(255,255,255,0.02); }
</style>
""", unsafe_allow_html=True)

exigir_login()

st.title("Lançamentos")
st.markdown("<span style='color: #A0AEC0;'>Registre suas entradas e saídas financeiras conectadas às suas contas e categorias.</span>", unsafe_allow_html=True)

# ==========================================
# NOVAS FUNÇÕES DE BANCO DE DADOS (Híbridas)
# ==========================================
def conectar():
    db_nome = st.session_state.get("db_nome", "financas.db")
    conn, engine = conectar_banco(db_nome)
    return conn, engine

def executar_sql(conn, engine, query, params=()):
    # Se for Postgres, troca os "?" do SQLite por "%s" para não dar erro
    if engine == "postgres" and params:
        query = query.replace("?", "%s")
    
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    try:
        return cur.lastrowid
    except:
        return 0

# -----------------------------
# Helpers
# -----------------------------
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
NOME_PARA_NUMERO = {v: k for k, v in MESES_PT.items()}

def fmt_brl(valor: float) -> str:
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def parse_valor_brl(txt: str) -> float:
    try:
        s = str(txt)
        s = re.sub(r"[^\d,.-]", "", s)
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except:
        return 0.0

def limpar_txt(x) -> str:
    s = "" if x is None else str(x)
    return (s.replace("\\n", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ").strip())

def badge_tipo(tipo: str) -> str:
    tipo = limpar_txt(tipo)
    if tipo == "Entrada":
        color = "#00CC96" 
        icon = "▲"
    else:
        color = "#FF4B4B" 
        icon = "▼"
    return f'<span style="color:{color}; font-weight:700;">{icon} {tipo}</span>'

def badge_status_minimal(status: str, atrasado: bool) -> str:
    status = limpar_txt(status)

    if atrasado:
        cor_bg = "rgba(255,75,75,0.12)"
        cor_tx = "#FF4B4B"
        icon = icon_svg("alert")
        texto = "Atrasado"
    elif status == "Realizado":
        cor_bg = "rgba(0,204,150,0.12)"
        cor_tx = "#00CC96"
        icon = icon_svg("check")
        texto = "Realizado"
    else:
        cor_bg = "rgba(249,199,79,0.12)"
        cor_tx = "#F9C74F"
        icon = icon_svg("clock")
        texto = "Previsto"

    return f"""<span style="display:inline-flex; align-items:center; gap:8px; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:700; color:{cor_tx}; background:{cor_bg}; border:1px solid rgba(255,255,255,0.08); white-space:nowrap;"><span style="display:inline-flex; color:{cor_tx};">{icon}</span>{texto}</span>"""

def seletor_data_ptbr(prefix_key: str, label: str, default: date):
    st.markdown(f"**{label}**")
    c1, c2, c3 = st.columns([1.3, 2, 1.6])

    with c2:
        mes_op = list(MESES_PT.values())
        mes_label = st.selectbox("Mês", options=mes_op, index=default.month - 1, key=f"{prefix_key}_mes")
        mes = NOME_PARA_NUMERO[mes_label]

    with c3:
        ano_op = list(range(default.year - 5, default.year + 6))
        ano_op_str = [str(a) for a in ano_op]
        ano = st.selectbox("Ano", options=ano_op_str, index=ano_op_str.index(str(default.year)), key=f"{prefix_key}_ano")

    try:
        max_dia = calendar.monthrange(int(ano), int(mes))[1]
    except:
        max_dia = 31

    dia_default = min(int(default.day), int(max_dia))

    with c1:
        dia = st.selectbox("Dia", options=list(range(1, int(max_dia) + 1)), index=dia_default - 1, format_func=lambda x: f"{x:02d}", key=f"{prefix_key}_dia")

    return date(int(ano), int(mes), int(dia))

def garantir_audit_log():
    conn, engine = conectar()
    executar_sql(conn, engine, """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT,
            usuario TEXT,
            acao TEXT,
            detalhes TEXT
        )
    """)
    conn.close()

def registrar_log(acao: str, detalhes: str):
    try:
        conn, engine = conectar()
        usuario = st.session_state.get("usuario_atual", "desconhecido")
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        executar_sql(conn, engine, "INSERT INTO audit_log (data_hora, usuario, acao, detalhes) VALUES (?, ?, ?, ?)", (agora, usuario, acao, detalhes))
        conn.close()
    except:
        pass

# -----------------------------
# DADOS INICIAIS
# -----------------------------
conn, engine = conectar()
df_contas = pd.read_sql_query("SELECT id, nome FROM accounts", conn)
df_categorias = pd.read_sql_query("SELECT id, nome, tipo FROM categories", conn)
conn.close()

if df_contas.empty or df_categorias.empty:
    st.warning("⚠️ Você precisa cadastrar pelo menos uma **Conta** e uma **Categoria** antes de fazer lançamentos.")
else:
    col_form, col_table = st.columns([1, 2])

    with col_form:
        st.subheader("Novo Registro")
        with st.form("form_lancamento", clear_on_submit=True):
            tipo = st.radio("Tipo de Movimentação", ["Entrada", "Saída"], horizontal=True)
            descricao = st.text_input("Descrição", placeholder="Ex: Pagamento Fornecedor X, Venda Y")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.00, format="%.2f")

            data_prevista = seletor_data_ptbr("novo", "Data Prevista / Vencimento", default=date.today())

            dict_contas = dict(zip(df_contas["nome"], df_contas["id"]))
            dict_categorias = dict(zip(df_categorias["nome"] + " (" + df_categorias["tipo"] + ")", df_categorias["id"]))

            conta_selecionada = st.selectbox("Conta", options=list(dict_contas.keys()))
            categoria_selecionada = st.selectbox("Categoria", options=list(dict_categorias.keys()))
            status = st.selectbox("Status", ["Previsto", "Realizado"])

            submit = st.form_submit_button("Salvar Lançamento", use_container_width=True)

            if submit:
                if descricao and valor > 0:
                    conta_id = dict_contas[conta_selecionada]
                    categoria_id = dict_categorias[categoria_selecionada]
                    data_real = data_prevista if status == "Realizado" else None

                    conn, engine = conectar()
                    executar_sql(conn, engine, """
                        INSERT INTO transactions (tipo, descricao, valor, data_prevista, data_real, status, conta_id, categoria_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (tipo, descricao, valor, data_prevista, data_real, status, conta_id, categoria_id))
                    conn.close()

                    st.success("Lançamento salvo com sucesso!")
                    st.rerun()
                else:
                    st.error("⚠️ Preencha a descrição e informe um valor maior que zero.")

    with col_table:
        st.subheader("Últimos Lançamentos")

        hoje = date.today()
        ano_atual = hoje.year
        mes_atual = hoje.month

        anos_opcoes = list(range(ano_atual - 3, ano_atual + 2))
        meses_opcoes = list(MESES_PT.values())

        f1, f2, f3 = st.columns([1.2, 1.6, 2.2])
        with f1:
            ano_sel = st.selectbox("Ano", options=anos_opcoes, index=anos_opcoes.index(ano_atual))
        with f2:
            mes_sel_label = st.selectbox("Mês", options=meses_opcoes, index=mes_atual - 1)
            mes_sel = NOME_PARA_NUMERO[mes_sel_label]
        with f3:
            busca_desc = st.text_input("Buscar na descrição", placeholder="Digite para filtrar...")

        f4, f5, f6, f7 = st.columns([1.4, 1.4, 1.6, 1.6])
        with f4:
            status_sel = st.selectbox("Status", options=["Todos", "Previsto", "Realizado", "Atrasado"])
        with f5:
            tipo_sel = st.selectbox("Tipo", options=["Todos", "Entrada", "Saída"])
        with f6:
            categoria_sel = st.selectbox("Categoria", options=["Todas"] + sorted(df_categorias["nome"].unique().tolist()))
        with f7:
            conta_sel = st.selectbox("Conta", options=["Todas"] + sorted(df_contas["nome"].unique().tolist()))

        conn, engine = conectar()
        query = """
            SELECT t.id as ID, t.status as Status, t.data_prevista as Data, t.tipo as Tipo, t.descricao as Descrição, c.nome as Categoria, a.nome as Conta, t.valor as Valor
            FROM transactions t
            LEFT JOIN categories c ON t.categoria_id = c.id
            LEFT JOIN accounts a ON t.conta_id = a.id
            ORDER BY t.id DESC
        """
        df_transacoes = pd.read_sql_query(query, conn)
        conn.close()

        if not df_transacoes.empty:
            df_transacoes["Status"] = df_transacoes["Status"].apply(limpar_txt)
            df_transacoes["Data_dt"] = pd.to_datetime(df_transacoes["Data"], errors="coerce")
            df_transacoes["Valor_num"] = pd.to_numeric(df_transacoes["Valor"], errors="coerce").fillna(0.0)

            df_filtrado = df_transacoes[(df_transacoes["Data_dt"].dt.year == int(ano_sel)) & (df_transacoes["Data_dt"].dt.month == int(mes_sel))].copy()
            df_filtrado["Atrasado"] = (df_filtrado["Status"] == "Previsto") & (df_filtrado["Data_dt"].dt.date < hoje)

            if status_sel == "Atrasado":
                df_filtrado = df_filtrado[df_filtrado["Atrasado"] == True]
            elif status_sel != "Todos":
                df_filtrado = df_filtrado[df_filtrado["Status"] == status_sel]

            if tipo_sel != "Todos":
                df_filtrado = df_filtrado[df_filtrado["Tipo"] == tipo_sel]

            if categoria_sel != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Categoria"] == categoria_sel]

            if conta_sel != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Conta"] == conta_sel]

            if busca_desc.strip():
                df_filtrado = df_filtrado[df_filtrado["Descrição"].astype(str).str.contains(busca_desc.strip(), case=False, na=False)]

            if df_filtrado.empty:
                st.info("Nenhum lançamento encontrado com os filtros selecionados.")
            else:
                df_view = df_filtrado.copy()
                df_view["Data"] = df_view["Data_dt"].dt.strftime("%d/%m/%Y")
                df_view["Valor"] = df_view["Valor_num"].apply(fmt_brl)
                df_view["Status"] = df_view.apply(lambda r: badge_status_minimal(r["Status"], bool(r["Atrasado"])), axis=1)
                df_view["Tipo"] = df_view["Tipo"].apply(badge_tipo)
                df_view = df_view.drop(columns=["ID", "Data_dt", "Valor_num", "Atrasado"], errors="ignore")

                st.write("")
                e1, e2 = st.columns([1, 1])

                df_export = df_filtrado.copy()
                df_export["Data"] = df_export["Data_dt"].dt.strftime("%d/%m/%Y")
                df_export["Valor"] = df_export["Valor_num"].apply(fmt_brl)
                df_export["Status"] = df_export.apply(lambda r: "Atrasado" if bool(r["Atrasado"]) else str(r["Status"]), axis=1)
                df_export = df_export.drop(columns=["ID", "Data_dt", "Valor_num", "Atrasado"], errors="ignore")

                with e1:
                    csv_data = df_export.to_csv(index=False, sep=";").encode("utf-8")
                    st.download_button("Baixar CSV", data=csv_data, file_name=f"lancamentos_{ano_sel}_{mes_sel:02d}.csv", mime="text/csv", use_container_width=True)

                with e2:
                    try:
                        import io
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                            df_export.to_excel(writer, index=False, sheet_name="Lancamentos")
                        st.download_button("Baixar Excel", data=buffer.getvalue(), file_name=f"lancamentos_{ano_sel}_{mes_sel:02d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                    except:
                        st.warning("⚠️ Instale: `pip install openpyxl` para Excel")

                st.markdown(df_view.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("Nenhum lançamento registrado no sistema ainda.")

    st.divider()
    st.subheader("Gerenciar Lançamentos")

    conn, engine = conectar()
    df_raw = pd.read_sql_query("""
        SELECT t.id, t.tipo, t.descricao, t.valor, t.data_prevista, t.status, a.nome as conta_nome, c.nome as categoria_nome, t.conta_id, t.categoria_id
        FROM transactions t
        LEFT JOIN accounts a ON t.conta_id = a.id
        LEFT JOIN categories c ON t.categoria_id = c.id
        ORDER BY t.id DESC
    """, conn)
    conn.close()

    if not df_raw.empty:
        df_raw["valor_num"] = pd.to_numeric(df_raw.get("valor", 0), errors="coerce").fillna(0.0)
        df_raw["valor_fmt"] = df_raw["valor_num"].apply(fmt_brl)
        df_raw["data_fmt"] = pd.to_datetime(df_raw.get("data_prevista", None), errors="coerce").dt.strftime("%d/%m/%Y").fillna("—")
        df_raw["status"] = df_raw.get("status", "").astype(str).apply(limpar_txt)

        opcoes = df_raw.apply(lambda r: f"ID {r['id']} | {r['descricao']} - {r['valor_fmt']} ({r['status']}) | {r['data_fmt']}", axis=1).tolist()
        dict_opcoes = dict(zip(opcoes, df_raw["id"].tolist()))

        lancamento_selecionado = st.selectbox("Selecione o Lançamento:", options=opcoes)
        id_selecionado = dict_opcoes[lancamento_selecionado]
        linha = df_raw[df_raw["id"] == id_selecionado].iloc[0]

        st.write("")
        st.markdown("### Editar Lançamento")

        cE1, cE2 = st.columns([1, 1])
        with cE1:
            tipo_edit = st.selectbox("Tipo", options=["Entrada", "Saída"], index=0 if linha["tipo"] == "Entrada" else 1)
            descricao_edit = st.text_input("Descrição", value=str(linha["descricao"]))
            valor_edit_txt = st.text_input("Valor", value=str(linha["valor_fmt"]))

        with cE2:
            data_default = pd.to_datetime(linha["data_prevista"], errors="coerce")
            data_default = date.today() if pd.isna(data_default) else data_default.date()
            data_edit = seletor_data_ptbr("edit", "Data Prevista / Vencimento (Editar)", default=data_default)
            status_edit = st.selectbox("Status", options=["Previsto", "Realizado"], index=0 if linha["status"] == "Previsto" else 1)

        cE3, cE4 = st.columns([1, 1])
        with cE3:
            conta_nomes = df_contas["nome"].tolist()
            conta_index = conta_nomes.index(linha["conta_nome"]) if linha["conta_nome"] in conta_nomes else 0
            conta_edit_nome = st.selectbox("Conta (Editar)", options=conta_nomes, index=conta_index)
            conta_edit_id = int(df_contas[df_contas["nome"] == conta_edit_nome]["id"].iloc[0])

        with cE4:
            cat_nomes = df_categorias["nome"].tolist()
            cat_index = cat_nomes.index(linha["categoria_nome"]) if linha["categoria_nome"] in cat_nomes else 0
            categoria_edit_nome = st.selectbox("Categoria (Editar)", options=cat_nomes, index=cat_index)
            categoria_edit_id = int(df_categorias[df_categorias["nome"] == categoria_edit_nome]["id"].iloc[0])

        a1, a2, a3, a4 = st.columns([1, 1, 1, 1])

        with a1:
            if st.button("Salvar Alterações", type="primary", use_container_width=True):
                valor_edit = parse_valor_brl(valor_edit_txt)
                if not descricao_edit.strip() or valor_edit <= 0:
                    st.error("⚠️ Descrição não pode ficar vazia e o valor deve ser maior que zero.")
                else:
                    data_real = data_edit if status_edit == "Realizado" else None
                    conn, engine = conectar()
                    executar_sql(conn, engine, """
                        UPDATE transactions SET tipo = ?, descricao = ?, valor = ?, data_prevista = ?, data_real = ?, status = ?, conta_id = ?, categoria_id = ? WHERE id = ?
                    """, (tipo_edit, descricao_edit.strip(), float(valor_edit), data_edit, data_real, status_edit, conta_edit_id, categoria_edit_id, int(id_selecionado)))
                    conn.close()
                    st.success("✅ Lançamento atualizado com sucesso!")
                    st.rerun()

        with a2:
            if st.button("Duplicar", use_container_width=True):
                conn, engine = conectar()
                novo_id = executar_sql(conn, engine, """
                    INSERT INTO transactions (tipo, descricao, valor, data_prevista, data_real, status, conta_id, categoria_id)
                    SELECT tipo, descricao, valor, data_prevista, NULL, 'Previsto', conta_id, categoria_id FROM transactions WHERE id = ?
                """, (int(id_selecionado),))
                conn.close()
                st.success(f"✅ Lançamento duplicado com sucesso! Novo ID: {novo_id}")
                st.rerun()

        with a3:
            if st.button("Preparar Exclusão", use_container_width=True):
                st.session_state["confirmar_exclusao_id"] = int(id_selecionado)

        with a4:
            if st.session_state.get("confirmar_exclusao_id") == int(id_selecionado):
                if st.button("Confirmar Exclusão", type="secondary", use_container_width=True):
                    conn, engine = conectar()
                    executar_sql(conn, engine, "DELETE FROM transactions WHERE id = ?", (int(id_selecionado),))
                    conn.close()
                    st.session_state.pop("confirmar_exclusao_id", None)
                    st.success("✅ Lançamento apagado permanentemente!")
                    st.rerun()
