import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date

# 1) Configuração
st.set_page_config(
    page_title="Sistema Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"  # deixa a sidebar recolhida por padrão
)
st.logo("logo.png")

# ✅ AJUSTE DE LAYOUT (LOGIN MAIS EM CIMA + LOGO DO SIDEBAR MELHOR)
# (Somente CSS - não muda estrutura)
# ⚠️ CORREÇÃO: removi o margin-top negativo no stForm que estava "sumindo" o login em algumas telas/temas
st.markdown("""
<style>
/* =========================
   1) Puxa o conteúdo um pouco pra cima (sem quebrar o login)
   ========================= */
.block-container{
    padding-top: 0.55rem !important;
}

/* Em algumas versões o Streamlit coloca um espaçador no topo */
[data-testid="stAppViewContainer"] > .main{
    padding-top: 0rem !important;
}

/* NÃO mexer no stForm com margin negativo aqui (isso foi o que fez sumir pra você) */
/* div[data-testid="stForm"]{ margin-top: -18px !important; } */

/* =========================
   2) Sidebar: melhora o logo acima do menu
   ========================= */
[data-testid="stSidebarHeader"]{
    padding-top: 10px !important;
    padding-bottom: 10px !important;
}

[data-testid="stSidebar"] img{
    max-width: 100% !important;
    height: auto !important;
}

[data-testid="stSidebar"] [data-testid="stImage"]{
    display: flex !important;
    justify-content: center !important;
}

[data-testid="stSidebar"]{
    border-right: 1px solid rgba(255,255,255,0.06);
}
</style>
""", unsafe_allow_html=True)

# 2) Segurança
from auth import checar_senha, fazer_logout
if not checar_senha():
    st.stop()

# -----------------------------
# Helpers visuais e formatação
# -----------------------------
MESES_PT = {
    1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
    7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"
}

def fmt_brl(x: float) -> str:
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def icon_svg(name: str) -> str:
    icons = {
        "trend": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M4 16l6-6 4 4 6-6" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M14 8h6v6" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
        "wallet": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M3 7.5C3 6.12 4.12 5 5.5 5H19a2 2 0 0 1 2 2v2H7a2 2 0 0 0-2 2v6.5A2.5 2.5 0 0 1 3 17V7.5Z" stroke="rgba(255,255,255,.85)" stroke-width="1.6"/>
          <path d="M7 9h14v8a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2Z" stroke="rgba(255,255,255,.85)" stroke-width="1.6"/>
          <path d="M17 13h2" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round"/>
        </svg>""",
        "in": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M12 20V4" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M7 9l5-5 5 5" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
        "out": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M12 4v16" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M7 15l5 5 5-5" stroke="rgba(255,255,255,.85)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
    }
    return icons.get(name, "")

def metric_card(title: str, value: str, footer_text: str, footer_color: str, icon_html: str = ""):
    # footer_color: "green" | "red" | "gray"
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
          <div style="font-weight:900;font-size:14px;opacity:.92;">{title}</div>
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
# Topbar (D.Tech + usuário + sair)
# -----------------------------
empresa = st.session_state.get("empresa", "")
usuario = st.session_state.get("usuario_atual", "")

t1, t2, t3 = st.columns([2.2, 3.6, 1.4])
with t1:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="width:34px;height:34px;border-radius:10px;background:rgba(255,255,255,.06);display:flex;align-items:center;justify-content:center;font-weight:900;">
        D
      </div>
      <div>
        <div style="font-size:14px;opacity:.85;font-weight:800;">D.Tech</div>
        <div style="font-size:12px;opacity:.65;margin-top:-2px;">Gestão Financeira</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with t2:
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:center;gap:10px;">
      <div style="font-size:20px;font-weight:900;">Painel Executivo</div>
      <div style="opacity:.7;">|</div>
      <div style="opacity:.85;font-weight:800;">{empresa}</div>
    </div>
    """, unsafe_allow_html=True)

with t3:
    st.markdown(f"""
    <div style="text-align:right;opacity:.85;font-size:13px;margin-top:6px;">
      Usuário: <b>{usuario}</b>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True, key="btn_sair_home"):
        fazer_logout()

st.markdown("Visão estratégica consolidada para tomada de decisão.")
st.divider()

# -----------------------------
# Menu superior
# -----------------------------
menu = st.tabs(["Visão Geral", "Análise Visual"])

def conectar():
    return sqlite3.connect(st.session_state["db_nome"])

# -----------------------------
# Dados
# -----------------------------
conn = conectar()
df = pd.read_sql_query("""
    SELECT 
        t.tipo,
        t.valor,
        t.data_prevista,
        t.data_real,
        t.status,
        c.nome as categoria
    FROM transactions t
    LEFT JOIN categories c ON t.categoria_id = c.id
""", conn)
conn.close()

if df.empty:
    st.info("Bem-vindo! Cadastre contas, categorias e lançamentos para visualizar seu painel.")
    st.stop()

df["data_prevista"] = pd.to_datetime(df["data_prevista"], errors="coerce").dt.date
df["data_real"] = pd.to_datetime(df["data_real"], errors="coerce").dt.date

hoje = date.today()
mes_atual = hoje.month
ano_atual = hoje.year
mes_nome = MESES_PT.get(mes_atual, "Mês")
titulo_mes = f"{mes_nome} / {ano_atual}"

# -----------------------------
# KPIs
# -----------------------------
df_realizado = df[df["status"] == "Realizado"]

total_entradas_reais = df_realizado[df_realizado["tipo"] == "Entrada"]["valor"].sum()
total_saidas_reais = df_realizado[df_realizado["tipo"] == "Saída"]["valor"].sum()
saldo_atual = float(total_entradas_reais - total_saidas_reais)

df_mes_previsto = df[
    (pd.to_datetime(df["data_prevista"]).dt.month == mes_atual) &
    (pd.to_datetime(df["data_prevista"]).dt.year == ano_atual)
]
df_mes_realizado = df_realizado[
    (pd.to_datetime(df_realizado["data_real"]).dt.month == mes_atual) &
    (pd.to_datetime(df_realizado["data_real"]).dt.year == ano_atual)
]

total_receber_mes = float(df_mes_previsto[(df_mes_previsto["tipo"] == "Entrada") & (df_mes_previsto["status"] == "Previsto")]["valor"].sum())
total_pagar_mes = float(df_mes_previsto[(df_mes_previsto["tipo"] == "Saída") & (df_mes_previsto["status"] == "Previsto")]["valor"].sum())
resultado_mes = float(df_mes_realizado[df_mes_realizado["tipo"] == "Entrada"]["valor"].sum() - df_mes_realizado[df_mes_realizado["tipo"] == "Saída"]["valor"].sum())

# -----------------------------
# ABA 1: Visão Geral
# -----------------------------
with menu[0]:
    st.subheader(f"Resumo de {titulo_mes}")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Saldo atual em caixa",
            fmt_brl(saldo_atual),
            "Dinheiro real disponível",
            "green" if saldo_atual >= 0 else "red",
            icon_svg("wallet")
        )

    with c2:
        metric_card(
            "A receber (mês)",
            fmt_brl(total_receber_mes),
            "Previsto para entrar",
            "green",
            icon_svg("in")
        )

    with c3:
        metric_card(
            "A pagar (mês)",
            fmt_brl(total_pagar_mes),
            "Previsto para sair",
            "red" if total_pagar_mes > 0 else "green",
            icon_svg("out")
        )

    with c4:
        metric_card(
            "Resultado do mês",
            fmt_brl(resultado_mes),
            "Lucro/Prejuízo realizado",
            "green" if resultado_mes >= 0 else "red",
            icon_svg("trend")
        )

# -----------------------------
# ABA 2: Análise Visual
# -----------------------------
with menu[1]:
    st.subheader("Análise Visual")

    g1, g2 = st.columns(2)

    with g1:
        st.markdown("**Receitas vs Despesas (Realizado no mês)**")
        dados_barras = pd.DataFrame({
            "Tipo": ["Entradas", "Saídas"],
            "Valor": [
                float(df_mes_realizado[df_mes_realizado["tipo"] == "Entrada"]["valor"].sum()),
                float(df_mes_realizado[df_mes_realizado["tipo"] == "Saída"]["valor"].sum())
            ]
        })
        fig_barras = px.bar(
            dados_barras, x="Tipo", y="Valor", color="Tipo",
            text_auto=".2s", template="plotly_dark"
        )
        fig_barras.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_barras, use_container_width=True)

    with g2:
        st.markdown("**Despesas por categoria (Previsto no mês)**")
        df_despesas = df_mes_previsto[df_mes_previsto["tipo"] == "Saída"]
        if not df_despesas.empty:
            df_pizza = df_despesas.groupby("categoria")["valor"].sum().reset_index()
            fig_pizza = px.pie(
                df_pizza, values="valor", names="categoria", hole=0.4,
                template="plotly_dark"
            )
            fig_pizza.update_traces(textposition="inside", textinfo="percent+label")
            fig_pizza.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Nenhuma despesa prevista para este mês.")
