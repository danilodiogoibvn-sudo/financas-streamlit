import streamlit as st
import pandas as pd
from datetime import date
import base64
import streamlit.components.v1 as components
import google.generativeai as genai

from style import carregar_estilos
from auth import exigir_login
from database import conectar_banco

# ==========================================
# 1) CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Consultor IA | D.Tech", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2) TRUQUE MÁGICO DO IPHONE
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
        """, height=0, width=0
    )
except:
    pass

try: st.logo("logo.png")
except: pass

carregar_estilos()
exigir_login()

usuario_logado = st.session_state.get("usuario_atual", "danilo")
empresa = st.session_state.get("empresa", "sua empresa")

st.title("✨ Consultor Financeiro com IA")
st.markdown("<span style='color: #A0AEC0;'>Receba conselhos estratégicos, alertas de gastos e planos de economia baseados nos seus números reais.</span>", unsafe_allow_html=True)
st.divider()

# ==========================================
# BANCO DE DADOS HÍBRIDO
# ==========================================
def conectar():
    db_nome = st.session_state.get("db_nome", "financeiro.db")
    conn, engine = conectar_banco(db_nome)
    return conn, engine

# -----------------------------
# Extração de Dados do Mês Atual
# -----------------------------
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
if engine == "postgres": query = query.replace("?", "%s")
df = pd.read_sql_query(query, conn, params=(usuario_logado,))
conn.close()

# Processamento
df["data_real"] = pd.to_datetime(df["data_real"], errors="coerce")
df_mes = df[(df["data_real"].dt.month == mes_atual) & (df["data_real"].dt.year == ano_atual)]

entradas = df_mes[df_mes["tipo"] == "Entrada"]["valor"].sum()
saidas = df_mes[df_mes["tipo"] == "Saída"]["valor"].sum()
saldo = entradas - saidas

# Pega as 3 categorias com maiores gastos
df_saidas = df_mes[df_mes["tipo"] == "Saída"]
if not df_saidas.empty:
    top_categorias = df_saidas.groupby("categoria")["valor"].sum().sort_values(ascending=False).head(3)
    texto_categorias = ", ".join([f"{cat} (R$ {val:,.2f})" for cat, val in top_categorias.items()])
else:
    texto_categorias = "Nenhuma despesa registrada no mês."

# -----------------------------
# Interface e Configuração da IA
# -----------------------------
st.markdown("### Configuração da Inteligência Artificial")
st.info("Para gerar o relatório, o sistema utiliza a inteligência artificial do Google (Gemini).")

# Busca a chave na nuvem (st.secrets) ou pede pro usuário digitar
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = st.text_input("Cole sua Chave de API do Gemini (API Key) para liberar o acesso:", type="password")
    if not api_key:
        st.warning("⚠️ Você precisa de uma API Key gratuita do Google AI Studio para usar esta função.")
        st.stop()

# -----------------------------
# Geração do Insight
# -----------------------------
st.write("")
if st.button("🧠 Gerar Análise Financeira do Mês", type="primary", use_container_width=True):
    with st.spinner("Analisando seus dados e escrevendo o relatório..."):
        try:
            # Configura a IA
            genai.configure(api_key=api_key)
            modelo = genai.GenerativeModel('gemini-2.5-flash')
            
            # O "Prompt Invisível" que cria a mágica
            prompt = f"""
            Você é um consultor financeiro sênior extremamente analítico, gentil e direto ao ponto. 
            Seu cliente é a empresa '{empresa}'. 
            
            Aqui estão os dados financeiros do mês atual:
            - Total de Receitas: R$ {entradas:,.2f}
            - Total de Despesas: R$ {saidas:,.2f}
            - Saldo do Mês: R$ {saldo:,.2f}
            - Maiores fontes de despesa (Top 3): {texto_categorias}
            
            Com base EXCLUSIVAMENTE nestes números, escreva um resumo estratégico para o dono da empresa. 
            Sua resposta deve conter:
            1. Um diagnóstico rápido da saúde financeira deste mês.
            2. Um alerta construtivo sobre onde ele gastou mais.
            3. Duas dicas práticas de onde ele poderia economizar ou onde deveria focar para o próximo mês.
            
            Escreva em tom profissional, mas encorajador. Formate com negritos e marcadores para facilitar a leitura.
            """
            
            # Chama a IA
            resposta = modelo.generate_content(prompt)
            
            # Exibe o resultado com visual premium
            st.success("Análise concluída com sucesso!")
            st.markdown("""
            <div style="background-color: rgba(0, 209, 255, 0.05); border: 1px solid rgba(0, 209, 255, 0.3); border-radius: 10px; padding: 20px;">
            """, unsafe_allow_html=True)
            
            st.markdown(resposta.text)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao conectar com a inteligência artificial: {e}")
            st.caption("Verifique se a sua API Key está correta e se você tem conexão com a internet.")
