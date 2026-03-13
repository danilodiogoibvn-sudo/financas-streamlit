import streamlit as st


def carregar_estilos():
    COR_PRIMARIA = "#00D1FF"
    COR_FUNDO_1 = "#090B14"
    COR_FUNDO_2 = "#151A2C"

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
       AJUSTES GLOBAIS
       ========================= */
    .block-container {{
        padding-top: 1.5rem !important;
        color: #FFFFFF;
    }}

    [data-testid="stSidebar"] {{
        color: #FFFFFF;
    }}

    /* =========================
       INPUTS E BOTÕES
       ========================= */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {{
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
        padding: 20px 20px 58px 20px;
        border-radius: 16px;
        border: 1px solid rgba(0, 209, 255, 0.15);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transition: all 0.25s ease-in-out;
        position: relative;
        overflow: hidden;
        min-height: 220px;
        height: 100%;
        box-sizing: border-box;
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
        word-break: break-word;
    }}

    .kpi-footer {{
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        padding: 10px 18px;
        border-top: 1px solid rgba(255,255,255,.05);
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 800;
        font-size: 12px;
        border-bottom-left-radius: 16px;
        border-bottom-right-radius: 16px;
        box-sizing: border-box;
    }}

    .kpi-footer-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 4px;
        flex-shrink: 0;
    }}

    /* =========================
       TABS
       ========================= */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 14px;
    }}

    .stTabs [data-baseweb="tab"] {{
        color: #A0AEC0;
        font-weight: 700;
    }}

    .stTabs [aria-selected="true"] {{
        color: #00D1FF !important;
    }}

    /* =========================
       PLOTLY / GRÁFICOS
       ========================= */
    .js-plotly-plot, .plotly {{
        border-radius: 16px;
    }}

    /* =========================
       RESPONSIVIDADE
       ========================= */
    @media (max-width: 900px) {{
        .kpi-card {{
            min-height: 200px;
            padding: 18px 18px 56px 18px;
        }}

        .kpi-value {{
            font-size: 24px;
        }}

        .kpi-title {{
            font-size: 12px;
        }}

        .kpi-footer {{
            font-size: 11px;
            padding: 10px 14px;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
   