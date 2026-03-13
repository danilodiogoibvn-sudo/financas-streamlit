import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

from database import inicializar_banco, conectar_banco
from auth import checar_senha, fazer_logout  # se seu arquivo for auth.py minúsculo, troque aqui

# --- IMPORTANDO SEUS NOVOS MÓDULOS D.TECH ---
from style import carregar_estilos
from components import metric_card, icon_svg

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

# Aplica toda a identidade visual de uma vez só!
carregar_estilos()

# 2) Segurança
if not checar_senha():
    st.stop()

# -----------------------------
# Helpers visuais e formatação
# -----------------------------
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def fmt_brl(x: float) -> str:
    try:
        return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

# -----------------------------
# Conexão (SQLite local / Neon no Cloud) via database.py
# -----------------------------
def conectar():
    """
    Usa o valor já salvo pelo Auth.py em st.session_state["db_nome"].
    - Local: "financas.db" / "dominio.db"
    - Cloud (Neon): "postgresql://..."
    """
    db_ref = st.session_state.get("db_nome")

    # fallback local (caso rode sem passar pelo fluxo normal)
    if not db_ref:
        db_ref = "financas.db"
        st.session_state["db_nome"] = db_ref

    conn, engine = conectar_banco(db_ref)
    return conn, engine

# ✅ Garante tabelas antes do SELECT (SQLite ou Neon)
inicializar_banco(st.session_state.get("db_nome", "financas.db"))

# -----------------------------
# Topbar (D.Tech + usuário + sair)
# -----------------------------
empresa = st.session_state.get("empresa", "")
usuario = st.session_state.get("usuario_atual", "")

t1, t2, t3 = st.columns([2.2, 3.6, 1.4])
with t1:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="width:34px;height:34px;border-radius:10px;background:rgba(0,209,255,.1); color:#00D1FF; display:flex;align-items:center;justify-content:center;font-weight:900;">
        D
      </div>
      <div>
        <div style="font-size:14px;opacity:.85;font-weight:800; color:#FFFFFF;">D.Tech</div>
        <div style="font-size:12px;opacity:.65;margin-top:-2px; color:#A0AEC0;">Gestão Financeira</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with t2:
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:center;gap:10px;">
      <div style="font-size:20px;font-weight:900; color:#FFFFFF;">Painel Executivo</div>
      <div style="opacity:.5; color:#FFFFFF;">|</div>
      <div style="opacity:.85;font-weight:800; color:#00D1FF;">{empresa}</div>
    </div>
    """, unsafe_allow_html=True)

with t3:
    st.markdown(f"""
    <div style="text-align:right;opacity:.85;font-size:13px;margin-top:6px; color:#FFFFFF;">
      Usuário: <b>{usuario}</b>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True, key="btn_sair_home"):
        fazer_logout()

st.markdown("<span style='color: #A0AEC0;'>Visão estratégica consolidada para tomada de decisão.</span>", unsafe_allow_html=True)
st.divider()

# -----------------------------
# Menu superior
# -----------------------------
menu = st.tabs(["Visão Geral", "Análise Visual"])

# -----------------------------
# Dados
# -----------------------------
conn, engine = conectar()
try:
    # Sem parâmetros aqui, então funciona igual nos dois bancos
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
finally:
    conn.close()

if df.empty:
    st.info("Bem-vindo! Cadastre contas, categorias e lançamentos para visualizar seu painel.")
    st.stop()

# Padronização básica para evitar erros de acentuação/capitalização
df["tipo"] = df["tipo"].astype(str).str.strip()
df["status"] = df["status"].astype(str).str.strip()
if "categoria" in df.columns:
    df["categoria"] = df["categoria"].fillna("Sem categoria")

df["data_prevista"] = pd.to_datetime(df["data_prevista"], errors="coerce")
df["data_real"] = pd.to_datetime(df["data_real"], errors="coerce")

hoje = date.today()
mes_atual = hoje.month
ano_atual = hoje.year
mes_nome = MESES_PT.get(mes_atual, "Mês")
titulo_mes = f"{mes_nome} / {ano_atual}"

# -----------------------------
# KPIs
# -----------------------------
df_realizado = df[df["status"].str.lower() == "realizado"]

total_entradas_reais = float(df_realizado[df_realizado["tipo"] == "Entrada"]["valor"].sum())
total_saidas_reais = float(df_realizado[df_realizado["tipo"] == "Saída"]["valor"].sum())
saldo_atual = float(total_entradas_reais - total_saidas_reais)

df_mes_previsto = df[
    (df["data_prevista"].dt.month == mes_atual) &
    (df["data_prevista"].dt.year == ano_atual)
]

df_mes_realizado = df_realizado[
    (df_realizado["data_real"].dt.month == mes_atual) &
    (df_realizado["data_real"].dt.year == ano_atual)
]

total_receber_mes = float(
    df_mes_previsto[
        (df_mes_previsto["tipo"] == "Entrada") &
        (df_mes_previsto["status"].str.lower() == "previsto")
    ]["valor"].sum()
)

total_pagar_mes = float(
    df_mes_previsto[
        (df_mes_previsto["tipo"] == "Saída") &
        (df_mes_previsto["status"].str.lower() == "previsto")
    ]["valor"].sum()
)

resultado_mes = float(
    df_mes_realizado[df_mes_realizado["tipo"] == "Entrada"]["valor"].sum()
    - df_mes_realizado[df_mes_realizado["tipo"] == "Saída"]["valor"].sum()
)

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
        st.markdown("*Receitas vs Despesas (Realizado no mês)*")
        dados_barras = pd.DataFrame({
            "Tipo": ["Entradas", "Saídas"],
            "Valor": [
                float(df_mes_realizado[df_mes_realizado["tipo"] == "Entrada"]["valor"].sum()),
                float(df_mes_realizado[df_mes_realizado["tipo"] == "Saída"]["valor"].sum())
            ]
        })

        # Alterei para puxar a cor Ciano do layout
        fig_barras = px.bar(
            dados_barras,
            x="Tipo",
            y="Valor",
            color="Tipo",
            color_discrete_map={"Entradas": "#00CC96", "Saídas": "#FF4B4B"},
            text_auto=".2s",
            template="plotly_dark"
        )
        fig_barras.update_layout(
            showlegend=False, 
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_barras, use_container_width=True)

    with g2:
        st.markdown("*Despesas por categoria (Previsto no mês)*")
        df_despesas = df_mes_previsto[df_mes_previsto["tipo"] == "Saída"]

        if not df_despesas.empty:
            df_pizza = df_despesas.groupby("categoria", dropna=False)["valor"].sum().reset_index()

            fig_pizza = px.pie(
                df_pizza,
                values="valor",
                names="categoria",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Teal, # Cores mais focadas em azul/ciano
                template="plotly_dark"
            )
            fig_pizza.update_traces(textposition="inside", textinfo="percent+label")
            fig_pizza.update_layout(
                margin=dict(l=0, r=0, t=30, b=0), 
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Nenhuma despesa prevista para este mês.")
