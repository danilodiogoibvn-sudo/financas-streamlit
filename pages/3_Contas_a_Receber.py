import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta

from style import carregar_estilos
from components import metric_card, icon_svg
from auth import exigir_login
from database import conectar_banco

# 1) Configuração
st.set_page_config(
    page_title="Contas a Pagar | D.Tech", 
    page_icon="logo.png",  # <-- O SEGREDO ESTÁ AQUI!
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
.dt-table tbody td { padding:12px 12px; border-bottom:1px solid rgba(255,255,255,0.05); vertical-align:middle; }
.dt-table tbody tr:hover td { background:rgba(255,255,255,0.02); }
.dt-table tbody td:nth-child(1) { text-align:left; }
.dt-table tbody td:nth-child(2) { text-align:center; }
.dt-table tbody td:nth-child(5) { text-align:right; }
</style>
""", unsafe_allow_html=True)

exigir_login()

st.title("Contas a Receber")
st.markdown("<span style='color: #A0AEC0;'>Acompanhe previsões de recebimento e pagamentos confirmados.</span>", unsafe_allow_html=True)

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
    1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril", 5:"Maio", 6:"Junho",
    7:"Julho", 8:"Agosto", 9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro"
}
NOME_PARA_NUMERO = {v: k for k, v in MESES_PT.items()}

def fmt_brl(x: float) -> str:
    try: return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

def limpar_txt(x: str) -> str:
    try: return str(x).replace("\n", " ").strip()
    except: return ""

def badge_status_minimal_receber(status: str) -> str:
    s = limpar_txt(status)
    if s == "Recebido":
        cor_bg, cor_tx, icon, texto = "rgba(0,204,150,0.12)", "#00CC96", icon_svg("check"), "Realizado"
    elif s == "Atrasado":
        cor_bg, cor_tx, icon, texto = "rgba(255,75,75,0.12)", "#FF4B4B", icon_svg("alert"), "Atrasado"
    elif s == "Recebe em 7 dias":
        cor_bg, cor_tx, icon, texto = "rgba(249,199,79,0.12)", "#F9C74F", icon_svg("calendar"), "Recebe em 7 dias"
    else:
        cor_bg, cor_tx, icon, texto = "rgba(249,199,79,0.12)", "#F9C74F", icon_svg("clock"), "A receber"

    return f"""<span style="display:inline-flex; align-items:center; gap:8px; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:700; color:{cor_tx}; background:{cor_bg}; border:1px solid rgba(255,255,255,0.08); white-space:nowrap;"><span style="display:inline-flex; color:{cor_tx};">{icon}</span>{texto}</span>"""

# -----------------------------
# Dados
# -----------------------------
conn, engine = conectar()
df = pd.read_sql_query("""
    SELECT t.id, t.descricao as Cliente_Descricao, c.nome as Categoria, t.data_prevista as Previsao_Recebimento, t.valor as Valor, t.status as Status_BD
    FROM transactions t
    LEFT JOIN categories c ON t.categoria_id = c.id
    WHERE t.tipo = 'Entrada'
    ORDER BY t.data_prevista ASC
""", conn)
conn.close()

if df.empty:
    st.info("Nenhuma receita registrada ainda. Cadastre em 'Lançamentos'.")
    st.stop()

for col in ["Cliente_Descricao", "Categoria", "Status_BD"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace("\n", " ", regex=False).str.strip()

df["Previsao_Recebimento"] = pd.to_datetime(df["Previsao_Recebimento"], errors="coerce").dt.date
df["Prev_dt"] = pd.to_datetime(df["Previsao_Recebimento"], errors="coerce")

hoje = date.today()
em_7 = hoje + timedelta(days=7)

def definir_status(row):
    if row["Status_BD"] == "Realizado": return "Recebido"
    if row["Previsao_Recebimento"] is None: return "A receber"
    if row["Previsao_Recebimento"] < hoje: return "Atrasado"
    if hoje <= row["Previsao_Recebimento"] <= em_7: return "Recebe em 7 dias"
    return "A receber"

df["Status"] = df.apply(definir_status, axis=1)

# -----------------------------
# Filtros
# -----------------------------
st.subheader("Filtros")

ano_atual, mes_atual = hoje.year, hoje.month
anos = list(range(ano_atual - 3, ano_atual + 2))
meses_nomes = list(MESES_PT.values())
mes_atual_nome = MESES_PT[mes_atual]

f1, f2, f3 = st.columns([1.1, 1.6, 2.2])
with f1: ano_sel = st.selectbox("Ano", options=anos, index=anos.index(ano_atual))
with f2:
    mes_nome = st.selectbox("Mês", options=meses_nomes, index=meses_nomes.index(mes_atual_nome))
    mes_sel = NOME_PARA_NUMERO[mes_nome]
with f3: busca = st.text_input("Buscar cliente/descrição", placeholder="Ex: venda, pix, cartão...")

f4, f5, f6 = st.columns([1.6, 1.6, 1.2])
with f4: status_filtro = st.multiselect("Status", options=["Atrasado", "Recebe em 7 dias", "A receber", "Recebido"], default=["Atrasado", "Recebe em 7 dias", "A receber"])
with f5:
    cats = sorted([c for c in df["Categoria"].dropna().unique().tolist()])
    categoria_sel = st.multiselect("Categoria", options=cats, default=[])
with f6: ordenar = st.selectbox("Ordenar", options=["Previsão (mais próximo)", "Valor (maior)", "Valor (menor)"])

df_f = df[(df["Prev_dt"].dt.year == int(ano_sel)) & (df["Prev_dt"].dt.month == int(mes_sel))].copy()

if status_filtro: df_f = df_f[df_f["Status"].isin(status_filtro)]
if categoria_sel: df_f = df_f[df_f["Categoria"].isin(categoria_sel)]
if busca.strip(): df_f = df_f[df_f["Cliente_Descricao"].astype(str).str.contains(busca.strip(), case=False, na=False)]

if not df_f.empty:
    vmin, vmax = float(df_f["Valor"].min()), float(df_f["Valor"].max())
    if vmin < vmax:
        faixa = st.slider("Faixa de valor (R$)", min_value=vmin, max_value=vmax, value=(vmin, vmax))
        df_f = df_f[(df_f["Valor"] >= faixa[0]) & (df_f["Valor"] <= faixa[1])]
    else:
        st.info(f"Faixa de valor: apenas um valor → {fmt_brl(vmin)}")

if ordenar == "Valor (maior)": df_f = df_f.sort_values("Valor", ascending=False)
elif ordenar == "Valor (menor)": df_f = df_f.sort_values("Valor", ascending=True)
else: df_f = df_f.sort_values("Previsao_Recebimento", ascending=True)

# -----------------------------
# Resumo
# -----------------------------
st.divider()
st.subheader("Resumo")

total_receber = df_f[df_f["Status"].isin(["A receber", "Recebe em 7 dias"])]["Valor"].sum()
total_atrasado = df_f[df_f["Status"] == "Atrasado"]["Valor"].sum()
total_recebido = df_f[df_f["Status"] == "Recebido"]["Valor"].sum()
qtd_7 = df_f[df_f["Status"] == "Recebe em 7 dias"].shape[0]

m1, m2, m3, m4 = st.columns(4)
with m1: metric_card("Total a receber", fmt_brl(total_receber), "Previsto para entrar", "green", icon_svg("calendar"))
with m2: metric_card("Atrasado", fmt_brl(total_atrasado), "Tudo em dia!" if total_atrasado == 0 else "Cobrar clientes / repasse", "green" if total_atrasado == 0 else "red", icon_svg("alert"))
with m3: metric_card("Recebido", fmt_brl(total_recebido), "Visão do período filtrado", "green", icon_svg("check"))
with m4: metric_card("Recebe em 7 dias", str(qtd_7), "Prioridade", "green" if qtd_7 == 0 else "red", icon_svg("calendar"))

# -----------------------------
# Ação rápida
# -----------------------------
st.divider()
st.subheader("Ação rápida")

df_acao = df_f[df_f["Status_BD"] != "Realizado"].copy()
if df_acao.empty:
    st.info("Nada para marcar como recebido com os filtros atuais.")
else:
    df_acao["prev_fmt"] = pd.to_datetime(df_acao["Previsao_Recebimento"]).dt.strftime("%d/%m/%Y")
    df_acao["valor_fmt"] = df_acao["Valor"].apply(fmt_brl)

    op = df_acao.apply(lambda r: f"{limpar_txt(r['Cliente_Descricao'])} | {r['prev_fmt']} | {r['valor_fmt']} | {r['Status']}", axis=1).tolist()
    map_id = dict(zip(op, df_acao["id"].tolist()))

    cA1, cA2 = st.columns([3, 1])
    with cA1:
        escolha = st.selectbox("Selecione a entrada:", options=op)
        id_sel = int(map_id[escolha])
    with cA2:
        if st.button("Marcar como recebido", type="primary", use_container_width=True):
            st.session_state["confirmar_recebido_id"] = id_sel

    if st.session_state.get("confirmar_recebido_id") == id_sel:
        st.warning("Confirme: isso marcará como Realizado.")
        if st.button("Confirmar recebimento", use_container_width=True):
            conn, engine = conectar()
            try:
                executar_sql(conn, engine, "UPDATE transactions SET status='Realizado', data_real=? WHERE id=?", (date.today(), id_sel))
                st.success("Recebimento confirmado.")
                st.session_state.pop("confirmar_recebido_id", None)
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                conn.close()

# -----------------------------
# Tabela Detalhada
# -----------------------------
st.divider()
st.subheader("Lista")

if df_f.empty:
    st.success("Nenhum recebimento encontrado para os filtros.")
else:
    df_view = df_f[["Status", "Previsao_Recebimento", "Cliente_Descricao", "Categoria", "Valor"]].copy()
    df_view.rename(columns={"Previsao_Recebimento": "Data", "Cliente_Descricao": "Descrição"}, inplace=True)
    df_view["Descrição"] = df_view["Descrição"].apply(limpar_txt)
    df_view["Categoria"] = df_view["Categoria"].apply(limpar_txt)
    df_view["Data"] = pd.to_datetime(df_view["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_view["Valor"] = df_view["Valor"].apply(fmt_brl)
    df_view["Status"] = df_view["Status"].apply(badge_status_minimal_receber)

    df_export = df_f[["Status", "Previsao_Recebimento", "Cliente_Descricao", "Categoria", "Valor"]].copy()
    df_export.rename(columns={"Previsao_Recebimento": "Data", "Cliente_Descricao": "Descrição"}, inplace=True)
    df_export["Descrição"] = df_export["Descrição"].apply(limpar_txt)
    df_export["Categoria"] = df_export["Categoria"].apply(limpar_txt)
    df_export["Data"] = pd.to_datetime(df_export["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_export["Valor"] = df_export["Valor"].apply(fmt_brl)
    df_export["Status"] = df_export["Status"].astype(str).str.replace("\n", " ", regex=False).str.strip()

    e1, e2 = st.columns([1, 1])
    with e1:
        st.download_button("Baixar CSV", data=df_export.to_csv(index=False, sep=";").encode("utf-8"), file_name=f"contas_a_receber_{ano_sel}_{mes_sel:02d}.csv", mime="text/csv", use_container_width=True)
    with e2:
        try:
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Contas a Receber")
            st.download_button("Baixar Excel", data=buf.getvalue(), file_name=f"contas_a_receber_{ano_sel}_{mes_sel:02d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except:
            st.warning("Para baixar Excel: pip install openpyxl")

    st.markdown(f'<div class="dt-table">{df_view.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
