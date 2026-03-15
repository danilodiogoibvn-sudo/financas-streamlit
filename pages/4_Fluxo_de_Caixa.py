import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date, timedelta, datetime, timezone

from style import carregar_estilos
from components import metric_card, icon_svg
from auth import exigir_login
from database import conectar_banco

# 1) Configuração
st.set_page_config(
    page_title="Fluxo de Caixa | D.Tech", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

try:
    st.logo("logo.png")
except:
    pass

carregar_estilos()

exigir_login()

# Captura quem é o usuário logado agora
usuario_logado = st.session_state.get("usuario_atual", "danilo")

st.title("Fluxo de Caixa")
st.markdown("<span style='color: #A0AEC0;'>Visão diária das entradas, saídas e evolução do saldo acumulado.</span>", unsafe_allow_html=True)

# ==========================================
# BANCO DE DADOS HÍBRIDO
# ==========================================
def conectar():
    db_nome = st.session_state.get("db_nome", "financeiro.db")
    conn, engine = conectar_banco(db_nome)
    return conn, engine

# -----------------------------
# Helpers
# -----------------------------
def fmt_brl(x: float) -> str:
    try: return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

# 🚀 NOVA FUNÇÃO: Forçar o Fuso Horário do Brasil (Brasília UTC-3)
def obter_hoje_br():
    fuso_br = timezone(timedelta(hours=-3))
    return datetime.now(fuso_br).date()

# -----------------------------
# Período
# -----------------------------
st.subheader("Período")

# Agora o sistema sempre vai saber o dia correto no Brasil!
hoje = obter_hoje_br()
primeiro_dia_mes = hoje.replace(day=1)
ultimo_dia_mes = (primeiro_dia_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

cA, cB, cC = st.columns([1.2, 1.2, 2])

with cA: preset = st.selectbox("Atalho", ["Este mês", "Últimos 30 dias", "Últimos 90 dias", "Personalizado"], index=0)
with cB: base = st.selectbox("Base", ["Previsto (data_prevista)", "Realizado (data_real)"], index=0)

if preset == "Este mês": data_inicio_padrao, data_fim_padrao = primeiro_dia_mes, ultimo_dia_mes
elif preset == "Últimos 30 dias": data_inicio_padrao, data_fim_padrao = hoje - timedelta(days=30), hoje
elif preset == "Últimos 90 dias": data_inicio_padrao, data_fim_padrao = hoje - timedelta(days=90), hoje
else: data_inicio_padrao, data_fim_padrao = primeiro_dia_mes, ultimo_dia_mes

with cC:
    d1, d2 = st.columns(2)
    with d1: data_inicio = st.date_input("Data inicial", value=data_inicio_padrao, disabled=(preset != "Personalizado"), format="DD/MM/YYYY")
    with d2: data_fim = st.date_input("Data final", value=data_fim_padrao, disabled=(preset != "Personalizado"), format="DD/MM/YYYY")

if data_fim < data_inicio:
    data_inicio, data_fim = data_fim, data_inicio

# -----------------------------
# Dados (Filtrados por dono)
# -----------------------------
conn, engine = conectar()
if base.startswith("Realizado"):
    query = "SELECT tipo, valor, data_real as data_base FROM transactions WHERE data_real IS NOT NULL AND usuario_dono = ?"
else:
    query = "SELECT tipo, valor, data_prevista as data_base FROM transactions WHERE usuario_dono = ?"

if engine == "postgres": query = query.replace("?", "%s")
df = pd.read_sql_query(query, conn, params=(usuario_logado,))
conn.close()

if df.empty:
    st.info("Nenhuma movimentação registrada para gerar o fluxo de caixa.")
    st.stop()

df["data_base"] = pd.to_datetime(df["data_base"], errors="coerce").dt.date
df = df.dropna(subset=["data_base"])

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

df_agrupado = df_periodo.pivot_table(index="data_base", columns="tipo", values="valor", aggfunc="sum").fillna(0)

if "Entrada" not in df_agrupado.columns: df_agrupado["Entrada"] = 0.0
if "Saída" not in df_agrupado.columns: df_agrupado["Saída"] = 0.0

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

with m1: metric_card("Saldo inicial", fmt_brl(saldo_inicial), "Antes do período", "gray", icon_svg("wallet"))
with m2: metric_card("Entradas", fmt_brl(total_entradas), "Receitas no período", "green", icon_svg("up"))
with m3: metric_card("Saídas", fmt_brl(total_saidas), "Despesas no período", "red" if total_saidas > 0 else "green", icon_svg("down"))
with m4: metric_card("Saldo final", fmt_brl(saldo_final), f"Resultado: {fmt_brl(resultado)}", "green" if saldo_final >= 0 else "red", icon_svg("trend"))

# -----------------------------
# Gráficos
# -----------------------------
st.divider()
st.subheader("Evolução do saldo e movimentações")

g1, g2 = st.columns([2, 1])

with g1:
    fig_line = px.line(
        df_agrupado, x="Data", y="Saldo Acumulado", markers=True,
        labels={"Data": "Data", "Saldo Acumulado": "Saldo (R$)"}, template="plotly_dark"
    )
    cor_linha = "#00D1FF" if saldo_final >= 0 else "#FF4B4B"
    fig_line.update_traces(line=dict(color=cor_linha, width=3), marker=dict(size=7))
    fig_line.update_layout(margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_line, use_container_width=True)

with g2:
    df_totais = pd.DataFrame({"Tipo": ["Entradas", "Saídas"], "Valor": [total_entradas, total_saidas]})
    fig_bar = px.bar(
        df_totais, x="Tipo", y="Valor", color="Tipo", 
        color_discrete_map={"Entradas": "#00D1FF", "Saídas": "#FF4B4B"}, 
        text_auto=".2s", template="plotly_dark"
    )
    fig_bar.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
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
        st.download_button("Baixar CSV", data=csv_data, file_name=f"fluxo_caixa_{data_inicio}_{data_fim}.csv", mime="text/csv", use_container_width=True)
    with e2:
        try:
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_tabela.to_excel(writer, index=False, sheet_name="Fluxo de Caixa")
            st.download_button("Baixar Excel", data=buf.getvalue(), file_name=f"fluxo_caixa_{data_inicio}_{data_fim}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except:
            st.warning("Para baixar Excel: pip install openpyxl")
