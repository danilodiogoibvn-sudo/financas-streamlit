import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

st.set_page_config(page_title="Fluxo de Caixa", page_icon="📊", layout="wide")
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


st.title("Fluxo de Caixa")
st.markdown("Visão diária das entradas, saídas e evolução do saldo acumulado.")

def conectar():
    return sqlite3.connect(st.session_state["db_nome"])

# -----------------------------
# Helpers
# -----------------------------
def fmt_brl(x: float) -> str:
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def icon_svg(name: str) -> str:
    icons = {
        "wallet": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M3 7.5C3 6.12 4.12 5 5.5 5H19a2 2 0 0 1 2 2v2H7a2 2 0 0 0-2 2v6.5A2.5 2.5 0 0 1 3 17V7.5Z" stroke="rgba(255,255,255,.85)" stroke-width="1.6"/>
          <path d="M7 9h14v8a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2Z" stroke="rgba(255,255,255,.85)" stroke-width="1.6"/>
          <path d="M17 13h2" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round"/>
        </svg>""",
        "up": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M12 4v16" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M7 9l5-5 5 5" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
        "down": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M12 20V4" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M7 15l5 5 5-5" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
        "trend": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M4 16l6-6 4 4 6-6" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M14 8h6v6" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
        "calendar": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M7 3v3M17 3v3" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M4 8h16" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M6 5h12a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" stroke="rgba(255,255,255,.85)" stroke-width="1.6"/>
        </svg>""",
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
          <div style="width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.06);">
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

# -----------------------------
# Período
# -----------------------------
st.subheader("Período")

hoje = date.today()
primeiro_dia_mes = hoje.replace(day=1)
ultimo_dia_mes = (primeiro_dia_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

cA, cB, cC = st.columns([1.2, 1.2, 2])

with cA:
    preset = st.selectbox("Atalho", ["Este mês", "Últimos 30 dias", "Últimos 90 dias", "Personalizado"], index=0)
with cB:
    base = st.selectbox("Base", ["Previsto (data_prevista)", "Realizado (data_real)"], index=0)

if preset == "Este mês":
    data_inicio_padrao, data_fim_padrao = primeiro_dia_mes, ultimo_dia_mes
elif preset == "Últimos 30 dias":
    data_inicio_padrao, data_fim_padrao = hoje - timedelta(days=30), hoje
elif preset == "Últimos 90 dias":
    data_inicio_padrao, data_fim_padrao = hoje - timedelta(days=90), hoje
else:
    data_inicio_padrao, data_fim_padrao = primeiro_dia_mes, ultimo_dia_mes

with cC:
    d1, d2 = st.columns(2)
    with d1:
        data_inicio = st.date_input("Data inicial", value=data_inicio_padrao, disabled=(preset != "Personalizado"))
    with d2:
        data_fim = st.date_input("Data final", value=data_fim_padrao, disabled=(preset != "Personalizado"))

if data_fim < data_inicio:
    data_inicio, data_fim = data_fim, data_inicio

# -----------------------------
# Dados
# -----------------------------
conn = conectar()
if base.startswith("Realizado"):
    df = pd.read_sql_query("SELECT tipo, valor, data_real as data_base FROM transactions WHERE data_real IS NOT NULL", conn)
else:
    df = pd.read_sql_query("SELECT tipo, valor, data_prevista as data_base FROM transactions", conn)
conn.close()

if df.empty:
    st.info("Nenhuma movimentação registrada para gerar o fluxo de caixa.")
    st.stop()

df["data_base"] = pd.to_datetime(df["data_base"], errors="coerce").dt.date
df = df.dropna(subset=["data_base"])

# saldo inicial
df_antes = df[df["data_base"] < data_inicio]
entradas_antes = df_antes[df_antes["tipo"] == "Entrada"]["valor"].sum()
saidas_antes = df_antes[df_antes["tipo"] == "Saída"]["valor"].sum()
saldo_inicial = float(entradas_antes - saidas_antes)

mask = (df["data_base"] >= data_inicio) & (df["data_base"] <= data_fim)
df_periodo = df[mask]

if df_periodo.empty:
    st.warning("Nenhum lançamento encontrado neste período.")
    metric_card("Saldo inicial", fmt_brl(saldo_inicial), "Antes do período", "gray", icon_svg("wallet"))
    st.stop()

df_agrupado = (
    df_periodo
    .pivot_table(index="data_base", columns="tipo", values="valor", aggfunc="sum")
    .fillna(0)
)

if "Entrada" not in df_agrupado.columns:
    df_agrupado["Entrada"] = 0.0
if "Saída" not in df_agrupado.columns:
    df_agrupado["Saída"] = 0.0

df_agrupado["Saldo do Dia"] = df_agrupado["Entrada"] - df_agrupado["Saída"]
df_agrupado["Saldo Acumulado"] = saldo_inicial + df_agrupado["Saldo do Dia"].cumsum()
df_agrupado = df_agrupado.reset_index().rename(columns={"data_base": "Data"})

total_entradas = float(df_agrupado["Entrada"].sum())
total_saidas = float(df_agrupado["Saída"].sum())
resultado = float(total_entradas - total_saidas)
saldo_final = float(df_agrupado["Saldo Acumulado"].iloc[-1])

# -----------------------------
# Resumo
# -----------------------------
st.divider()
st.subheader("Resumo do período")

m1, m2, m3, m4 = st.columns(4)

with m1:
    metric_card("Saldo inicial", fmt_brl(saldo_inicial), "Antes do período", "gray", icon_svg("wallet"))
with m2:
    metric_card("Entradas", fmt_brl(total_entradas), "Receitas no período", "green", icon_svg("up"))
with m3:
    metric_card("Saídas", fmt_brl(total_saidas), "Despesas no período", "red" if total_saidas > 0 else "green", icon_svg("down"))
with m4:
    metric_card("Saldo final", fmt_brl(saldo_final), f"Resultado: {fmt_brl(resultado)}",
                "green" if saldo_final >= 0 else "red", icon_svg("trend"))

# -----------------------------
# Gráficos
# -----------------------------
st.divider()
st.subheader("Evolução do saldo e movimentações")

g1, g2 = st.columns([2, 1])

with g1:
    fig_line = px.line(
        df_agrupado,
        x="Data",
        y="Saldo Acumulado",
        markers=True,
        labels={"Data": "Data", "Saldo Acumulado": "Saldo (R$)"},
        template="plotly_dark"
    )
    cor_linha = "#00CC96" if saldo_final >= 0 else "#EF553B"
    fig_line.update_traces(line=dict(color=cor_linha, width=3), marker=dict(size=7))
    fig_line.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_line, use_container_width=True)

with g2:
    df_totais = pd.DataFrame({"Tipo": ["Entradas", "Saídas"], "Valor": [total_entradas, total_saidas]})
    fig_bar = px.bar(df_totais, x="Tipo", y="Valor", text_auto=".2s", template="plotly_dark")
    fig_bar.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------
# Tabela + Export
# -----------------------------
st.divider()
with st.expander("Ver tabela detalhada dia a dia"):
    df_tabela = df_agrupado.copy()
    df_tabela["Data"] = pd.to_datetime(df_tabela["Data"]).dt.strftime("%d/%m/%Y")

    for col in ["Entrada", "Saída", "Saldo do Dia", "Saldo Acumulado"]:
        df_tabela[col] = df_tabela[col].apply(fmt_brl)

    st.dataframe(df_tabela, hide_index=True, use_container_width=True)

    e1, e2 = st.columns([1, 1])
    with e1:
        csv_data = df_tabela.to_csv(index=False, sep=";").encode("utf-8")
        st.download_button("Baixar CSV", data=csv_data, file_name=f"fluxo_caixa_{data_inicio}_{data_fim}.csv",
                           mime="text/csv", use_container_width=True)
    with e2:
        try:
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_tabela.to_excel(writer, index=False, sheet_name="Fluxo de Caixa")
            st.download_button("Baixar Excel", data=buf.getvalue(), file_name=f"fluxo_caixa_{data_inicio}_{data_fim}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except:
            st.warning("Para baixar Excel: pip install openpyxl")
