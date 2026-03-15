import streamlit as st
import pandas as pd
from datetime import date
import calendar
import base64
import streamlit.components.v1 as components
from google import genai

from style import carregar_estilos
from auth import exigir_login
from database import conectar_banco
from components import metric_card, icon_svg

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Consultor IA | D.Tech",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# ÍCONE IPHONE
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
        height=0,
        width=0
    )
except Exception:
    pass

try:
    st.logo("logo.png")
except Exception:
    pass

# ==========================================
# LOGIN + ESTILO
# ==========================================
carregar_estilos()
exigir_login()

usuario_logado = st.session_state.get("usuario_atual", "danilo")
empresa = st.session_state.get("empresa", "sua empresa")

st.title("✨ Consultor Financeiro com IA")
st.markdown(
    "<span style='color:#A0AEC0'>Receba conselhos estratégicos, alertas de gastos e planos de economia baseados nos seus números reais.</span>",
    unsafe_allow_html=True
)
st.divider()

# ==========================================
# BANCO DE DADOS E HELPERS
# ==========================================
def conectar():
    db_nome = st.session_state.get("db_nome", "financeiro.db")
    conn, engine = conectar_banco(db_nome)
    return conn, engine

def fmt_brl(x: float) -> str:
    try: return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

# ==========================================
# EXTRAÇÃO DE DADOS
# ==========================================
hoje = date.today()
mes_atual = hoje.month
ano_atual = hoje.year

# 🚀 NOVIDADE: Calculando quantos dias faltam para acabar o mês
ultimo_dia = calendar.monthrange(ano_atual, mes_atual)[1]
dias_restantes = ultimo_dia - hoje.day

conn, engine = conectar()

query = """
SELECT t.tipo, t.valor, t.data_real, c.nome as categoria
FROM transactions t
LEFT JOIN categories c ON t.categoria_id = c.id
WHERE t.usuario_dono = ? AND t.status = 'Realizado'
"""

if engine == "postgres":
    query = query.replace("?", "%s")

df = pd.read_sql_query(query, conn, params=(usuario_logado,))
conn.close()

if df.empty:
    df = pd.DataFrame(columns=["tipo", "valor", "data_real", "categoria"])

df["data_real"] = pd.to_datetime(df["data_real"], errors="coerce")

df_mes = df[
    (df["data_real"].dt.month == mes_atual) &
    (df["data_real"].dt.year == ano_atual)
].copy()

entradas = float(df_mes.loc[df_mes["tipo"] == "Entrada", "valor"].sum())
saidas = float(df_mes.loc[df_mes["tipo"] == "Saída", "valor"].sum())
saldo = entradas - saidas

df_saidas = df_mes[df_mes["tipo"] == "Saída"].copy()
df_saidas["categoria"] = df_saidas["categoria"].fillna("Sem categoria")

if not df_saidas.empty:
    top_categorias = (
        df_saidas.groupby("categoria")["valor"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
    )
    texto_categorias = "\n".join(
        [f"- {cat}: R$ {val:,.2f}" for cat, val in top_categorias.items()]
    )
else:
    texto_categorias = "- Nenhuma despesa registrada no mês."

# ==========================================
# RESUMO VISUAL (PADRÃO D.TECH!)
# ==========================================
col1, col2, col3 = st.columns(3)

with col1:
    metric_card("Receitas do mês", fmt_brl(entradas), "Total que entrou", "green", icon_svg("up"))

with col2:
    metric_card("Despesas do mês", fmt_brl(saidas), "Total que saiu", "red" if saidas > 0 else "gray", icon_svg("down"))

with col3:
    metric_card("Saldo do mês", fmt_brl(saldo), "Resultado parcial", "green" if saldo >= 0 else "red", icon_svg("wallet"))

st.markdown("### 🧠 Inteligência Financeira")
st.info("A análise é gerada automaticamente com base nos dados financeiros parciais do mês atual.")

# ==========================================
# CHAVE DA API VIA SECRETS
# ==========================================
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("A chave GEMINI_API_KEY não foi encontrada no Secrets do Streamlit.")
    st.stop()

# ==========================================
# BOTÃO GERAR ANÁLISE
# ==========================================
if st.button("🧠 Gerar Análise Financeira do Mês", use_container_width=True, type="primary"):
    with st.spinner("Analisando seus dados financeiros..."):
        try:
            client = genai.Client(api_key=api_key)

            # 🚀 NOVIDADE: O Prompt agora entende a passagem do tempo!
            prompt = f"""
            Você é um consultor financeiro especialista em gestão empresarial.
            Analise EXCLUSIVAMENTE os dados abaixo da empresa "{empresa}".

            CONTEXTO TEMPORAL IMPORTANTE:
            Hoje é dia {hoje.strftime('%d/%m/%Y')}. Faltam {dias_restantes} dias para o mês acabar. 
            Como o mês ainda está no meio/andamento, NÃO fale como se o mês estivesse fechado. 
            Seu foco deve ser em orientar o ritmo de gastos para o resto do mês e garantir que o caixa não fique no vermelho até o final.

            Dados parciais do mês atual:
            - Receitas totais até hoje: R$ {entradas:,.2f}
            - Despesas totais até hoje: R$ {saidas:,.2f}
            - Saldo atual: R$ {saldo:,.2f}

            Principais categorias de gastos até o momento:
            {texto_categorias}

            Monte uma resposta bonita, clara e profissional em português do Brasil com esta estrutura:

            ## Diagnóstico da Quinzena/Semana
            Faça um resumo de como está o ritmo financeiro da empresa considerando os dias que faltam para o mês acabar.

            ## Atenção ao Caixa
            Mostre onde estão os maiores gastos e se o ritmo de despesa está perigoso.

            ## Estratégia para o fim do mês
            Dê 2 dicas práticas e realistas do que ele deve fazer nos próximos {dias_restantes} dias.

            Regras:
            - Não invente números.
            - Baseie-se apenas nos dados informados.
            - Seja direto, útil e encorajador.
            """

            resposta = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            texto = getattr(resposta, "text", None)

            if not texto:
                st.warning("A IA não retornou texto na resposta.")
                st.stop()

            st.success("Análise concluída com sucesso!")

            st.markdown("""
            <div style="
                background-color: rgba(0,209,255,0.05);
                border:1px solid rgba(0,209,255,0.30);
                border-radius:14px;
                padding:22px;
                margin-top:10px;
            ">
            """, unsafe_allow_html=True)

            st.markdown(texto)

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erro ao gerar análise: {e}")
