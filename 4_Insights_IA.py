import streamlit as st
import pandas as pd
from datetime import date
import base64
import streamlit.components.v1 as components
from openai import OpenAI

from style import carregar_estilos
from auth import exigir_login
from database import conectar_banco

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
# ICONE IPHONE
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
except:
    pass

try:
    st.logo("logo.png")
except:
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
"""
<span style='color:#A0AEC0'>
Receba conselhos estratégicos, alertas de gastos e planos de economia baseados nos seus números reais.
</span>
""",
unsafe_allow_html=True
)

st.divider()

# ==========================================
# BANCO DE DADOS
# ==========================================

def conectar():
    db_nome = st.session_state.get("db_nome", "financeiro.db")
    conn, engine = conectar_banco(db_nome)
    return conn, engine


# ==========================================
# EXTRAÇÃO DE DADOS
# ==========================================

hoje = date.today()
mes_atual = hoje.month
ano_atual = hoje.year

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

df["data_real"] = pd.to_datetime(df["data_real"], errors="coerce")

df_mes = df[
    (df["data_real"].dt.month == mes_atual)
    & (df["data_real"].dt.year == ano_atual)
]

entradas = df_mes[df_mes["tipo"] == "Entrada"]["valor"].sum()
saidas = df_mes[df_mes["tipo"] == "Saída"]["valor"].sum()
saldo = entradas - saidas

df_saidas = df_mes[df_mes["tipo"] == "Saída"]

if not df_saidas.empty:

    top_categorias = (
        df_saidas.groupby("categoria")["valor"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
    )

    texto_categorias = ", ".join(
        [f"{cat} (R$ {val:,.2f})" for cat, val in top_categorias.items()]
    )

else:
    texto_categorias = "Nenhuma despesa registrada no mês."

# ==========================================
# CONFIGURAÇÃO DA IA
# ==========================================

st.markdown("### 🧠 Inteligência Financeira")

st.info("A análise é gerada por inteligência artificial baseada nos dados financeiros do mês atual.")

api_key = st.secrets.get("OPENAI_API_KEY", "")

if not api_key:

    st.warning("⚠️ Configure sua OPENAI_API_KEY no secrets do Streamlit.")
    st.stop()

# ==========================================
# BOTÃO GERAR RELATÓRIO
# ==========================================

if st.button("🧠 Gerar Análise Financeira do Mês", use_container_width=True):

    with st.spinner("Analisando seus dados financeiros..."):

        try:

            client = OpenAI(api_key=api_key)

            prompt = f"""
Você é um consultor financeiro especialista em gestão empresarial.

Empresa: {empresa}

Dados financeiros do mês atual:

Receitas totais: R$ {entradas:,.2f}
Despesas totais: R$ {saidas:,.2f}
Saldo final: R$ {saldo:,.2f}

Principais categorias de gastos:
{texto_categorias}

Crie um relatório estratégico contendo:

1️⃣ Diagnóstico da saúde financeira
2️⃣ Onde estão os maiores gastos
3️⃣ 2 sugestões práticas de economia
4️⃣ Estratégia para melhorar o próximo mês

Use português do Brasil.
Formate com títulos e bullet points.
"""

            resposta = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            texto = resposta.choices[0].message.content

            st.success("Análise concluída!")

            st.markdown(
"""
<div style="background-color: rgba(0,209,255,0.05);
border:1px solid rgba(0,209,255,0.3);
border-radius:10px;
padding:20px">
""",
unsafe_allow_html=True
)

            st.markdown(texto)

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:

            st.error(f"Erro ao gerar análise: {e}")
