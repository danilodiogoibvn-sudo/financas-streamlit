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

if df.empty:
    df = pd.DataFrame(columns=["tipo", "valor", "data_real", "categoria"])

df["data_real"] = pd.to_datetime(df["data_real"], errors="coerce")

df_mes = df[
    (df["data_real"].dt.month == mes_atual) &
    (df["data_real"].dt.year == ano_atual)
].copy()

entradas = df_mes.loc[df_mes["tipo"] == "Entrada", "valor"].sum()
saidas = df_mes.loc[df_mes["tipo"] == "Saída", "valor"].sum()
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
# CONFIGURAÇÃO IA
# ==========================================
st.markdown("### 🧠 Inteligência Financeira")
st.info("A análise é gerada automaticamente com base nos dados financeiros do mês atual.")

api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("A chave OPENAI_API_KEY não foi encontrada no Secrets do Streamlit.")
    st.stop()

# ==========================================
# BOTÃO
# ==========================================
if st.button("🧠 Gerar Análise Financeira do Mês", use_container_width=True, type="primary"):
    with st.spinner("Analisando seus dados financeiros..."):
        try:
            client = OpenAI(api_key=api_key)

            prompt = f"""
Você é um consultor financeiro especialista em gestão empresarial.

Analise EXCLUSIVAMENTE os dados abaixo da empresa "{empresa}".

Usuário dono da análise: {usuario_logado}

Dados do mês atual:
- Receitas totais: R$ {entradas:,.2f}
- Despesas totais: R$ {saidas:,.2f}
- Saldo final: R$ {saldo:,.2f}

Principais categorias de gastos:
{texto_categorias}

Monte uma resposta bonita, clara e profissional em português do Brasil com esta estrutura:

## Diagnóstico do mês
Faça um resumo objetivo da saúde financeira.

## Principais alertas
Mostre onde estão os maiores gastos e riscos.

## Oportunidades de economia
Dê 2 dicas práticas e realistas.

## Plano para o próximo mês
Sugira próximos passos financeiros.

Use linguagem encorajadora, profissional e fácil de entender.
"""

            resposta = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um consultor financeiro empresarial claro, estratégico e objetivo."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7
            )

            texto = resposta.choices[0].message.content

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