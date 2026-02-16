import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="Contas a Receber", page_icon="📊", layout="wide")
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

/* ✅ Título centralizado */
h1 { text-align: center !important; }
</style>
""", unsafe_allow_html=True)

from auth import exigir_login
exigir_login()


st.title("Contas a Receber")
st.markdown("Acompanhe previsões de recebimento e pagamentos confirmados.")

def conectar():
    return sqlite3.connect(st.session_state["db_nome"])

# -----------------------------
# Helpers (UI + formatação)
# -----------------------------
MESES_PT = {
    1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril", 5:"Maio", 6:"Junho",
    7:"Julho", 8:"Agosto", 9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro"
}
NOME_PARA_NUMERO = {v: k for k, v in MESES_PT.items()}

def fmt_brl(x: float) -> str:
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def icon_svg(name: str) -> str:
    # ✅ Ícones herdando cor do texto (currentColor)
    icons = {
        "calendar": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M7 3v3M17 3v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M4 8h16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M6 5h12a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" stroke="currentColor" stroke-width="1.6"/>
        </svg>""",
        "alert": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M12 9v4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M12 17h.01" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M10.3 4.9 3.5 17.2A2 2 0 0 0 5.2 20h13.6a2 2 0 0 0 1.7-2.8L13.7 4.9a2 2 0 0 0-3.4 0Z" stroke="currentColor" stroke-width="1.6"/>
        </svg>""",
        "check": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M20 6 9 17l-5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
        "clock": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M12 8v5l3 2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="currentColor" stroke-width="1.6"/>
        </svg>""",
        "wallet": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M3 7.5C3 6.12 4.12 5 5.5 5H19a2 2 0 0 1 2 2v2H7a2 2 0 0 0-2 2v6.5A2.5 2.5 0 0 1 3 17V7.5Z" stroke="currentColor" stroke-width="1.6"/>
          <path d="M7 9h14v8a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2Z" stroke="currentColor" stroke-width="1.6"/>
          <path d="M17 13h2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        </svg>"""
    }
    return icons.get(name, "")

def metric_card(title: str, value: str, footer_text: str, footer_color: str, icon_html: str = ""):
    color_map = {
        "green": ("rgba(0, 204, 150, 0.18)", "#00CC96", "↑"),
        "red": ("rgba(255, 75, 75, 0.18)", "#FF4B4B", "↓"),
        "gray": ("rgba(108, 117, 125, 0.18)", "#6C757D", "•"),
    }
    bg_footer, border_footer, seta = color_map.get(footer_color, color_map["gray"])

    st.markdown(f"""
    <div style="border:1px solid rgba(255,255,255,.10);border-radius:14px;background:rgba(255,255,255,.02);overflow:hidden;height:100%;">
      <div style="padding:14px 14px 10px 14px;">
        <div style="display:flex;gap:10px;align-items:center;margin-bottom:6px;">
          <div style="width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.06); color:rgba(255,255,255,.85);">
            {icon_html}
          </div>
          <div style="font-weight:800;font-size:14px;opacity:.92;">{title}</div>
        </div>
        <div style="font-size:26px;font-weight:900;letter-spacing:.2px;">{value}</div>
      </div>
      <div style="padding:10px 14px;background:{bg_footer};border-top:1px solid rgba(255,255,255,.08);display:flex;align-items:center;gap:8px;color:{border_footer};font-weight:900;font-size:12px;">
        <span style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:6px;border:1px solid {border_footer};">{seta}</span>
        <span>{footer_text}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

def limpar_txt(x: str) -> str:
    try:
        return str(x).replace("\n", " ").strip()
    except:
        return ""

def badge_status_minimal_receber(status: str) -> str:
    s = limpar_txt(status)

    if s == "Recebido":
        cor_bg = "rgba(0,204,150,0.12)"
        cor_tx = "#00CC96"
        icon = icon_svg("check")
        texto = "Realizado"
    elif s == "Atrasado":
        cor_bg = "rgba(255,75,75,0.12)"
        cor_tx = "#FF4B4B"
        icon = icon_svg("alert")
        texto = "Atrasado"
    elif s == "Recebe em 7 dias":
        cor_bg = "rgba(249,199,79,0.12)"
        cor_tx = "#F9C74F"
        icon = icon_svg("calendar")
        texto = "Recebe em 7 dias"
    else:
        cor_bg = "rgba(249,199,79,0.12)"
        cor_tx = "#F9C74F"
        icon = icon_svg("clock")
        texto = "A receber"

    return f"""<span style="display:inline-flex; align-items:center; gap:8px; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:700; color:{cor_tx}; background:{cor_bg}; border:1px solid rgba(255,255,255,0.08); white-space:nowrap;"><span style="display:inline-flex; color:{cor_tx};">{icon}</span>{texto}</span>"""

# -----------------------------
# CSS da tabela HTML (SaaS)
# -----------------------------
st.markdown("""
<style>
.dt-table table{ width:100%; border-collapse:separate; border-spacing:0; overflow:hidden; border-radius:14px; }
.dt-table thead th{
  text-align:center !important;
  font-weight:800;
  padding:12px 12px;
  border-bottom:1px solid rgba(255,255,255,0.10);
  background:rgba(255,255,255,0.02);
}
.dt-table tbody td{
  padding:12px 12px;
  border-bottom:1px solid rgba(255,255,255,0.06);
  vertical-align:middle;
}
.dt-table tbody tr:hover td{ background:rgba(255,255,255,0.02); }

/* alinhamentos por coluna (Status, Data, Descrição, Categoria, Valor) */
.dt-table tbody td:nth-child(1){ text-align:left; }
.dt-table tbody td:nth-child(2){ text-align:center; }
.dt-table tbody td:nth-child(5){ text-align:right; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Dados
# -----------------------------
conn = conectar()
df = pd.read_sql_query("""
    SELECT 
        t.id,
        t.descricao as Cliente_Descricao,
        c.nome as Categoria,
        t.data_prevista as Previsao_Recebimento,
        t.valor as Valor,
        t.status as Status_BD
    FROM transactions t
    LEFT JOIN categories c ON t.categoria_id = c.id
    WHERE t.tipo = 'Entrada'
    ORDER BY t.data_prevista ASC
""", conn)
conn.close()

if df.empty:
    st.info("Nenhuma receita registrada ainda. Cadastre em 'Lançamentos'.")
    st.stop()

# Limpeza do \n e espaços
for col in ["Cliente_Descricao", "Categoria", "Status_BD"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace("\n", " ", regex=False).str.strip()

df["Previsao_Recebimento"] = pd.to_datetime(df["Previsao_Recebimento"], errors="coerce").dt.date
df["Prev_dt"] = pd.to_datetime(df["Previsao_Recebimento"], errors="coerce")

hoje = date.today()
em_7 = hoje + timedelta(days=7)

def definir_status(row):
    if row["Status_BD"] == "Realizado":
        return "Recebido"
    if row["Previsao_Recebimento"] is None:
        return "A receber"
    if row["Previsao_Recebimento"] < hoje:
        return "Atrasado"
    if hoje <= row["Previsao_Recebimento"] <= em_7:
        return "Recebe em 7 dias"
    return "A receber"

df["Status"] = df.apply(definir_status, axis=1)

# -----------------------------
# Filtros
# -----------------------------
st.subheader("Filtros")

ano_atual, mes_atual = hoje.year, hoje.month
anos = list(range(ano_atual - 3, ano_atual + 2))

# ✅ Mês só nome (sem "(02)")
meses_nomes = list(MESES_PT.values())
mes_atual_nome = MESES_PT[mes_atual]

f1, f2, f3 = st.columns([1.1, 1.6, 2.2])
with f1:
    ano_sel = st.selectbox("Ano", options=anos, index=anos.index(ano_atual))
with f2:
    mes_nome = st.selectbox("Mês", options=meses_nomes, index=meses_nomes.index(mes_atual_nome))
    mes_sel = NOME_PARA_NUMERO[mes_nome]
with f3:
    busca = st.text_input("Buscar cliente/descrição", placeholder="Ex: venda, pix, cartão...")

f4, f5, f6 = st.columns([1.6, 1.6, 1.2])
with f4:
    status_filtro = st.multiselect(
        "Status",
        options=["Atrasado", "Recebe em 7 dias", "A receber", "Recebido"],
        default=["Atrasado", "Recebe em 7 dias", "A receber"]
    )
with f5:
    cats = sorted([c for c in df["Categoria"].dropna().unique().tolist()])
    categoria_sel = st.multiselect("Categoria", options=cats, default=[])
with f6:
    ordenar = st.selectbox("Ordenar", options=["Previsão (mais próximo)", "Valor (maior)", "Valor (menor)"])

df_f = df[(df["Prev_dt"].dt.year == int(ano_sel)) & (df["Prev_dt"].dt.month == int(mes_sel))].copy()

if status_filtro:
    df_f = df_f[df_f["Status"].isin(status_filtro)]
if categoria_sel:
    df_f = df_f[df_f["Categoria"].isin(categoria_sel)]
if busca.strip():
    df_f = df_f[df_f["Cliente_Descricao"].astype(str).str.contains(busca.strip(), case=False, na=False)]

# faixa (blindada)
if not df_f.empty:
    vmin, vmax = float(df_f["Valor"].min()), float(df_f["Valor"].max())
    if vmin < vmax:
        faixa = st.slider("Faixa de valor (R$)", min_value=vmin, max_value=vmax, value=(vmin, vmax))
        df_f = df_f[(df_f["Valor"] >= faixa[0]) & (df_f["Valor"] <= faixa[1])]
    else:
        st.info(f"Faixa de valor: apenas um valor → {fmt_brl(vmin)}")

# ordenação
if ordenar == "Valor (maior)":
    df_f = df_f.sort_values("Valor", ascending=False)
elif ordenar == "Valor (menor)":
    df_f = df_f.sort_values("Valor", ascending=True)
else:
    df_f = df_f.sort_values("Previsao_Recebimento", ascending=True)

# -----------------------------
# Resumo (cards com rodapé)
# -----------------------------
st.divider()
st.subheader("Resumo")

total_receber = df_f[df_f["Status"].isin(["A receber", "Recebe em 7 dias"])]["Valor"].sum()
total_atrasado = df_f[df_f["Status"] == "Atrasado"]["Valor"].sum()
total_recebido = df_f[df_f["Status"] == "Recebido"]["Valor"].sum()
qtd_7 = df_f[df_f["Status"] == "Recebe em 7 dias"].shape[0]

m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_card("Total a receber", fmt_brl(total_receber), "Previsto para entrar", "green", icon_svg("calendar"))
with m2:
    metric_card("Atrasado", fmt_brl(total_atrasado),
                "Tudo em dia!" if total_atrasado == 0 else "Cobrar clientes / repasse",
                "green" if total_atrasado == 0 else "red", icon_svg("alert"))
with m3:
    metric_card("Recebido (no filtro)", fmt_brl(total_recebido), "Visão do período filtrado", "green", icon_svg("check"))
with m4:
    metric_card("Recebe em 7 dias", str(qtd_7), "Prioridade", "green" if qtd_7 == 0 else "red", icon_svg("calendar"))

# -----------------------------
# Ação rápida: marcar como recebido
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
            conn = conectar()
            cur = conn.cursor()
            try:
                cur.execute("UPDATE transactions SET status='Realizado', data_real=? WHERE id=?", (date.today(), id_sel))
            except:
                cur.execute("UPDATE transactions SET status='Realizado' WHERE id=?", (id_sel,))
            conn.commit()
            conn.close()
            st.session_state.pop("confirmar_recebido_id", None)
            st.success("Recebimento confirmado.")
            st.rerun()

# -----------------------------
# Tabela + Export (SEM ID + sem \n)  ✅ PADRONIZADA
# -----------------------------
st.divider()
st.subheader("Lista")

if df_f.empty:
    st.success("Nenhum recebimento encontrado para os filtros.")
else:
    df_view = df_f[["Status", "Previsao_Recebimento", "Cliente_Descricao", "Categoria", "Valor"]].copy()
    df_view.rename(columns={
        "Previsao_Recebimento": "Data",
        "Cliente_Descricao": "Descrição"
    }, inplace=True)

    df_view["Descrição"] = df_view["Descrição"].apply(limpar_txt)
    df_view["Categoria"] = df_view["Categoria"].apply(limpar_txt)
    df_view["Data"] = pd.to_datetime(df_view["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_view["Valor"] = df_view["Valor"].apply(fmt_brl)

    # ✅ status com pill SaaS (sem emoji, ícone na mesma cor do texto)
    df_view["Status"] = df_view["Status"].apply(badge_status_minimal_receber)

    # Export (SEM HTML)
    df_export = df_f[["Status", "Previsao_Recebimento", "Cliente_Descricao", "Categoria", "Valor"]].copy()
    df_export.rename(columns={
        "Previsao_Recebimento": "Data",
        "Cliente_Descricao": "Descrição"
    }, inplace=True)
    df_export["Descrição"] = df_export["Descrição"].apply(limpar_txt)
    df_export["Categoria"] = df_export["Categoria"].apply(limpar_txt)
    df_export["Data"] = pd.to_datetime(df_export["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_export["Valor"] = df_export["Valor"].apply(fmt_brl)
    df_export["Status"] = df_export["Status"].astype(str).str.replace("\n", " ", regex=False).str.strip()

    e1, e2 = st.columns([1, 1])
    with e1:
        st.download_button(
            "Baixar CSV",
            data=df_export.to_csv(index=False, sep=";").encode("utf-8"),
            file_name=f"contas_a_receber_{ano_sel}_{mes_sel:02d}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with e2:
        try:
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Contas a Receber")
            st.download_button(
                "Baixar Excel",
                data=buf.getvalue(),
                file_name=f"contas_a_receber_{ano_sel}_{mes_sel:02d}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except:
            st.warning("Para baixar Excel: pip install openpyxl")

    st.markdown(f'<div class="dt-table">{df_view.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
