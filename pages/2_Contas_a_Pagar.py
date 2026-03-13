import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta

from style import carregar_estilos
from components import metric_card, icon_svg
from auth import exigir_login
from database import conectar_banco

st.set_page_config(page_title="Contas a Pagar", page_icon="📊", layout="wide")

try:
    st.logo("logo.png")
except:
    pass

carregar_estilos()

st.markdown("""
<style>
.dt-table table { width:100%; border-collapse:separate; border-spacing:0; overflow:hidden; border-radius:14px; }
.dt-table thead th {
    text-align:center !important;
    font-weight:800;
    padding:12px 12px;
    border-bottom:1px solid rgba(0, 209, 255, 0.3);
    background:rgba(0, 209, 255, 0.05);
    color: #00D1FF;
}
.dt-table tbody td {
    padding:12px 12px;
    border-bottom:1px solid rgba(255,255,255,0.05);
    vertical-align:middle;
}
.dt-table tbody tr:hover td { background:rgba(255,255,255,0.02); }
.dt-table tbody td:nth-child(1) { text-align:left; }
.dt-table tbody td:nth-child(2) { text-align:center; }
.dt-table tbody td:nth-child(5) { text-align:right; }
</style>
""", unsafe_allow_html=True)

exigir_login()

st.title("Contas a Pagar")
st.markdown("<span style='color: #A0AEC0;'>Acompanhe compromissos, fornecedores e evite atrasos.</span>", unsafe_allow_html=True)

# ==========================================
# BANCO DE DADOS HÍBRIDO
# ==========================================
def conectar():
    db_nome = st.session_state.get("db_nome", "financeiro.db") 
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

# -----------------------------
# Helpers
# -----------------------------
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
NOME_PARA_NUMERO = {v: k for k, v in MESES_PT.items()}

def fmt_brl(x: float) -> str:
    try: return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

def limpar_txt(x: str) -> str:
    try: return str(x).replace("\n", " ").strip()
    except: return ""

def badge_status_minimal(status: str, atrasado: bool) -> str:
    status = limpar_txt(status)

    if atrasado:
        cor_bg, cor_tx, icon, texto = "rgba(255,75,75,0.12)", "#FF4B4B", icon_svg("alert"), "Atrasado"
    elif status == "Realizado":
        cor_bg, cor_tx, icon, texto = "rgba(0,204,150,0.12)", "#00CC96", icon_svg("check"), "Realizado"
    else:
        cor_bg, cor_tx, icon, texto = "rgba(249,199,79,0.12)", "#F9C74F", icon_svg("clock"), "Previsto"

    return f"""<span style="display:inline-flex; align-items:center; gap:8px; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:700; color:{cor_tx}; background:{cor_bg}; border:1px solid rgba(255,255,255,0.08); white-space:nowrap;"><span style="display:inline-flex; color:{cor_tx};">{icon}</span>{texto}</span>"""

# -----------------------------
# Dados
# -----------------------------
try:
    conn, engine = conectar()
    df = pd.read_sql_query("""
        SELECT t.id, t.descricao as Fornecedor_Descricao, c.nome as Categoria, t.data_prevista as Vencimento, t.valor as Valor, t.status as Status_BD
        FROM transactions t
        LEFT JOIN categories c ON t.categoria_id = c.id
        WHERE t.tipo = 'Saída'
        ORDER BY t.data_prevista ASC
    """, conn)
    conn.close()
except Exception as e:
    st.error(f"Erro ao conectar banco: {e}")
    st.stop()

if df.empty:
    st.info("Nenhuma despesa registrada ainda.")

for col in ["Fornecedor_Descricao", "Categoria", "Status_BD"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace("\n", " ", regex=False).str.strip()

df["Vencimento"] = pd.to_datetime(df["Vencimento"], errors="coerce").dt.date
df["Venc_dt"] = pd.to_datetime(df["Vencimento"], errors="coerce")

hoje = date.today()
em_7 = hoje + timedelta(days=7)

def definir_status_label(row):
    if str(row["Status_BD"]) == "Realizado": return "Realizado"
    if row["Vencimento"] is None: return "A pagar"
    if row["Vencimento"] < hoje: return "Atrasado"
    if hoje <= row["Vencimento"] <= em_7: return "Recebe em 7 dias" # Mantendo a lógica do seu código original
    return "A pagar"

if not df.empty:
    df["Status_Label"] = df.apply(definir_status_label, axis=1)
else:
    df["Status_Label"] = []

# -----------------------------
# Filtros
# -----------------------------
st.subheader("Filtros")

ano_atual, mes_atual = hoje.year, hoje.month
anos = list(range(ano_atual - 3, ano_atual + 2))
lista_meses_nomes = list(MESES_PT.values())
nome_mes_atual = MESES_PT[mes_atual]

f1, f2, f3 = st.columns([1.1, 1.8, 2.2])
with f1: ano_sel = st.selectbox("Ano", options=anos, index=anos.index(ano_atual))
with f2:
    mes_selecionado_nome = st.selectbox("Mês", options=lista_meses_nomes, index=lista_meses_nomes.index(nome_mes_atual))
    mes_sel = NOME_PARA_NUMERO[mes_selecionado_nome]
with f3: busca = st.text_input("Buscar fornecedor/descrição", placeholder="Ex: aluguel, internet...")

f4, f5, f6 = st.columns([1.6, 1.6, 1.2])
STATUS_OPCOES = ["Atrasado", "Recebe em 7 dias", "A pagar", "Realizado"]

with f4: status_filtro = st.multiselect("Status", options=STATUS_OPCOES)
with f5:
    cats = sorted([c for c in df["Categoria"].dropna().unique().tolist()]) if not df.empty else []
    categoria_sel = st.multiselect("Categoria", options=cats)
with f6: ordenar = st.selectbox("Ordenar", options=["Vencimento (próximo)", "Valor (maior)", "Valor (menor)"])

df_f = pd.DataFrame()
if not df.empty:
    df_f = df[(df["Venc_dt"].dt.year == int(ano_sel)) & (df["Venc_dt"].dt.month == int(mes_sel))].copy()

    if status_filtro: df_f = df_f[df_f["Status_Label"].isin(status_filtro)]
    if categoria_sel: df_f = df_f[df_f["Categoria"].isin(categoria_sel)]
    if busca.strip(): df_f = df_f[df_f["Fornecedor_Descricao"].astype(str).str.contains(busca.strip(), case=False, na=False)]

    if ordenar == "Valor (maior)": df_f = df_f.sort_values("Valor", ascending=False)
    elif ordenar == "Valor (menor)": df_f = df_f.sort_values("Valor", ascending=True)
    else: df_f = df_f.sort_values("Vencimento", ascending=True)

# -----------------------------
# Resumo
# -----------------------------
st.divider()
st.subheader("Resumo")

if df_f.empty:
    st.info("Nenhum dado encontrado para este período.")
else:
    total_aberto = df_f[df_f["Status_Label"].isin(["A pagar", "Recebe em 7 dias"])]["Valor"].sum()
    total_atrasado = df_f[df_f["Status_Label"] == "Atrasado"]["Valor"].sum()
    total_pago = df_f[df_f["Status_Label"] == "Realizado"]["Valor"].sum()
    qtd_7 = df_f[df_f["Status_Label"] == "Recebe em 7 dias"].shape[0]

    m1, m2, m3, m4 = st.columns(4)
    with m1: metric_card("Total em aberto", fmt_brl(total_aberto), "A vencer + vencendo", "green", icon_svg("calendar"))
    with m2: metric_card("Total atrasado", fmt_brl(total_atrasado), "Atenção aos juros" if total_atrasado > 0 else "Tudo certo", "red" if total_atrasado > 0 else "green", icon_svg("alert"))
    with m3: metric_card("Total pago", fmt_brl(total_pago), "Neste filtro", "green", icon_svg("check"))
    with m4: metric_card("Vence em 7 dias", str(qtd_7), "Prioridade", "red" if qtd_7 > 0 else "green", icon_svg("calendar"))

# -----------------------------
# Ação Rápida
# -----------------------------
st.divider()
st.subheader("Ação rápida")

if not df_f.empty:
    df_acao = df_f[df_f["Status_BD"] != "Realizado"].copy()
    if df_acao.empty:
        st.info("Todas as contas deste período já foram pagas.")
    else:
        df_acao["venc_fmt"] = pd.to_datetime(df_acao["Vencimento"]).dt.strftime("%d/%m/%Y")
        df_acao["valor_fmt"] = df_acao["Valor"].apply(fmt_brl)

        opcoes = df_acao.apply(lambda r: f"{limpar_txt(r['Fornecedor_Descricao'])} | {r['venc_fmt']} | {r['valor_fmt']}", axis=1).tolist()
        map_id = dict(zip(opcoes, df_acao["id"].tolist()))

        cA1, cA2 = st.columns([3, 1])
        with cA1: escolha = st.selectbox("Selecione a conta para baixar:", options=opcoes)
        id_sel = map_id.get(escolha)

        with cA2:
            if st.button("Marcar como pago", type="primary", use_container_width=True):
                if id_sel:
                    conn, engine = conectar()
                    try:
                        executar_sql(conn, engine, "UPDATE transactions SET status='Realizado', data_real=? WHERE id=?", (date.today(), id_sel))
                        st.success("Conta atualizada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                    finally:
                        conn.close()

# -----------------------------
# Detalhamento
# -----------------------------
st.divider()
st.subheader("Detalhamento")

if not df_f.empty:
    df_view = df_f[["Status_BD", "Vencimento", "Fornecedor_Descricao", "Categoria", "Valor"]].copy()
    df_view.rename(columns={"Fornecedor_Descricao": "Descrição", "Vencimento": "Data", "Status_BD": "Status"}, inplace=True)
    df_view["Descrição"] = df_view["Descrição"].apply(limpar_txt)
    df_view["Categoria"] = df_view["Categoria"].apply(limpar_txt)
    df_view["Data"] = pd.to_datetime(df_view["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_view["Valor"] = df_view["Valor"].apply(fmt_brl)

    venc_dt = pd.to_datetime(df_f["Vencimento"], errors="coerce").dt.date
    atrasado_mask = (df_f["Status_BD"].astype(str) != "Realizado") & (venc_dt < hoje)

    df_view["Status"] = [badge_status_minimal(str(s), bool(a)) for s, a in zip(df_f["Status_BD"].astype(str).tolist(), atrasado_mask.tolist())]

    st.markdown(f'<div class="dt-table">{df_view.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

    df_export = df_f[["Status_Label", "Vencimento", "Fornecedor_Descricao", "Categoria", "Valor"]].copy()
    df_export.rename(columns={"Fornecedor_Descricao": "Descrição", "Vencimento": "Data", "Status_Label": "Status"}, inplace=True)
    df_export["Descrição"] = df_export["Descrição"].apply(limpar_txt)
    df_export["Categoria"] = df_export["Categoria"].apply(limpar_txt)
    df_export["Data"] = pd.to_datetime(df_export["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_export["Valor"] = df_export["Valor"].apply(fmt_brl)
    df_export["Status"] = df_export["Status"].astype(str).str.replace("\n", " ", regex=False).str.strip()

    c_exp1, c_exp2 = st.columns([1, 1])
    with c_exp1:
        csv = df_export.to_csv(index=False, sep=";").encode("utf-8")
        st.download_button("📥 Baixar CSV", data=csv, file_name=f"contas_pagar_{ano_sel}_{mes_sel}.csv", mime="text/csv", use_container_width=True)
    with c_exp2:
        try:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Contas")
            st.download_button("📥 Baixar Excel", data=buffer.getvalue(), file_name=f"contas_pagar_{ano_sel}_{mes_sel}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except:
            st.caption("Instale 'openpyxl' para baixar em Excel.")
