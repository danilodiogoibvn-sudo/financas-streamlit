import streamlit as st

def carregar_estilos():
    # CORES D.TECH
    COR_PRIMARIA = "#00D1FF" # Ciano Neon
    COR_FUNDO_1 = "#090B14"  # Fundo escuro (topo)
    COR_FUNDO_2 = "#151A2C"  # Fundo escuro (base)

    st.markdown(f"""
    <style>
    /* =========================
       FUNDO GERAL DA APLICAÇÃO
       ========================= */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(180deg, {COR_FUNDO_1} 0%, {COR_FUNDO_2} 100%) !important;
    }}
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: {COR_FUNDO_1} !important;
        border-right: 1px solid rgba(0, 209, 255, 0.1) !important;
    }}

    /* =========================
       AJUSTES GLOBAIS DE ESPAÇAMENTO E COR
       ========================= */
    .block-container {{
        padding-top: 1.5rem !important;
        color: #FFFFFF;
    }}
    [data-testid="stSidebar"] {{ color: #FFFFFF; }}

    /* =========================
       INPUTS E BOTÕES D.TECH
       ========================= */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {{
        color: #FFFFFF !important;
        background-color: rgba(255,255,255,0.02) !important;
        border: 1px solid rgba(0, 209, 255, 0.3) !important;
    }}
    
    div.stButton > button {{
        color: #FFFFFF !important;
        border: 1px solid {COR_PRIMARIA};
        background-color: rgba(0, 209, 255, 0.05);
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        background-color: {COR_PRIMARIA} !important;
        color: #000000 !important;
        box-shadow: 0 0 15px rgba(0, 209, 255, 0.4);
    }}

    /* =========================
       KPI CARD D.TECH
       ========================= */
    .kpi-card {{
        background: linear-gradient(145deg, rgba(21, 26, 44, 0.8), rgba(9, 11, 20, 0.9));
        padding: 20px 20px 45px 20px;
        border-radius: 16px;
        border: 1px solid rgba(0, 209, 255, 0.15);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transition: all 0.25s ease-in-out;
        position: relative;
        overflow: hidden;
        height: 100%;
    }}
    .kpi-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 15px 40px rgba(0, 209, 255, 0.15);
        border: 1px solid rgba(0, 209, 255, 0.6);
    }}
    .kpi-title {{
        font-size: 13px;
        color: #A0AEC0;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 700;
    }}
    .kpi-value {{
        font-size: 28px;
        font-weight: 900;
        line-height: 1.5;
        color: #FFFFFF;
        margin-top: 5px;
    }} 
    </style>
    """, unsafe_allow_html=True)
