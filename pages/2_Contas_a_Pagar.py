import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="Contas a Pagar", page_icon="📊", layout="wide")
# st.logo("logo.png") # Descomente se tiver o arquivo

# ============================
# UI COMPACTA (CSS PADRÃO)
# ============================
st.markdown("""
<style>
[data-testid="stSidebar"]{ width: 190px !important; min-width: 190px !important; }
section.main > div{ max-width: 100% !important; }
.block-container{ padding-left: 2.2rem !important; padding-right: 2.2rem !important; padding-top: 1.2rem !important; }
[data-testid="stSidebarNav"] li a{ padding-top: 6px !important; padding-bottom: 6px !important; }
h1, h2, h3 { margin-bottom: 0.2rem !important; }
</style>
""", unsafe_allow_html=True)

from auth import exigir_login
exigir_login()


st.title("Contas a Pagar")
st.markdown("Acompanhe compromissos, fornecedores e evite atrasos.")

# Ajuste para garantir que session_state do DB exista (mock para teste se necessário)
if "db_nome" not in st.session_state:
    st.session_state["db_nome"] = "financeiro.db"  # Nome padrão caso não venha do login

def conectar():
    return sqlite3.connect(st.session_state["db_nome"])

# -----------------------------
# Helpers
# -----------------------------
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
NOME_PARA_NUMERO = {v: k for k, v in MESES_PT.items()}

def fmt_brl(x: float) -> str:
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def limpar_txt(x: str) -> str:
    try:
        return str(x).replace("\n", " ").strip()
    except:
        return ""

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ÍCONES: AGORA USAM currentColor (pra ficar da cor do texto)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def icon_svg(name: str) -> str:
    icons = {
        "calendar": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M7 3v3M17 3v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            <path d="M4 8h16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            <path d="M6 5h12a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" stroke="currentColor" stroke-width="1.6"/>
        </svg>""",
        "alert": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 9v4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            <path d="M12 17h.01" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            <path d="M10.3 4.9 3.5 17.2A2 2 0 0 0 5.2 20h13.6a2 2 0 0 0 1.7-2.8L13.7 4.9a2 2 0 0 0-3.4 0Z" stroke="currentColor" stroke-width="1.6"/>
        </svg>""",
        "check": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M20 6 9 17l-5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
        "clock": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 8v5l3 2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="currentColor" stroke-width="1.6"/>
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
          <div style="width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.06);">{icon_html}</div>
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

def badge_status_minimal(status: str, atrasado: bool) -> str:
    status = limpar_txt(status)

    if atrasado:
        cor_bg = "rgba(255,75,75,0.12)"
        cor_tx = "#FF4B4B"
        icon = icon_svg("alert")
        texto = "Atrasado"
    elif status == "Realizado":
        cor_bg = "rgba(0,204,150,0.12)"
        cor_tx = "#00CC96"
        icon = icon_svg("check")
        texto = "Realizado"
    else:
        cor_bg = "rgba(249,199,79,0.12)"
        cor_tx = "#F9C74F"
        icon = icon_svg("clock")
        texto = "Previsto"

    # 1 LINHA só (sem \n)
    html = f"""<span style="display:inline-flex; align-items:center; gap:8px; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:700; color:{cor_tx}; background:{cor_bg}; border:1px solid rgba(255,255,255,0.08); white-space:nowrap;"><span style="display:inline-flex; color:{cor_tx};">{icon}</span>{texto}</span>"""
    return html

# -----------------------------
# Dados
# -----------------------------
try:
    conn = conectar()
    # Criar tabela se não existir (para garantir funcionamento standalone)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            categoria_id INTEGER,
            data_prevista DATE,
            valor REAL,
            status TEXT,
            tipo TEXT,
            data_real DATE
        )
    """)
    conn.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, nome TEXT)")

    df = pd.read_sql_query("""
        SELECT 
            t.id,
            t.descricao as Fornecedor_Descricao,
            c.nome as Categoria,
            t.data_prevista as Vencimento,
            t.valor as Valor,
            t.status as Status_BD
        FROM transactions t
        LEFT JOIN categories c ON t.categoria_id = c.id
        WHERE t.tipo = 'Saída'
        ORDER BY t.data_prevista ASC
    """, conn)
    conn.close()
except Exception as e:
    st.error(f"Erro ao conectar banco: {e}")
    st.stop()

if df.empty:
    st.info("Nenhuma despesa registrada ainda.")

# Limpeza e Tratamento
for col in ["Fornecedor_Descricao", "Categoria", "Status_BD"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace("\n", " ", regex=False).str.strip()

df["Vencimento"] = pd.to_datetime(df["Vencimento"], errors="coerce").dt.date
df["Venc_dt"] = pd.to_datetime(df["Vencimento"], errors="coerce")

hoje = date.today()
em_7 = hoje + timedelta(days=7)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# STATUS BASE (SEM EMOJI) — pra combinar com o filtro SaaS
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def definir_status_label(row):
    # status REAL do card/tela (não mexe no Status_BD)
    if str(row["Status_BD"]) == "Realizado":
        return "Realizado"
    if row["Vencimento"] is None:
        return "A receber"
    if row["Vencimento"] < hoje:
        return "Atrasado"
    if hoje <= row["Vencimento"] <= em_7:
        return "Recebe em 7 dias"
    return "A receber"

if not df.empty:
    df["Status_Label"] = df.apply(definir_status_label, axis=1)
else:
    df["Status_Label"] = []

# -----------------------------
# Filtros (MÊS SÓ NOME ✅)
# -----------------------------
st.subheader("Filtros")

ano_atual, mes_atual = hoje.year, hoje.month
anos = list(range(ano_atual - 3, ano_atual + 2))

lista_meses_nomes = list(MESES_PT.values())
nome_mes_atual = MESES_PT[mes_atual]

f1, f2, f3 = st.columns([1.1, 1.8, 2.2])
with f1:
    ano_sel = st.selectbox("Ano", options=anos, index=anos.index(ano_atual))
with f2:
    mes_selecionado_nome = st.selectbox(
        "Mês",
        options=lista_meses_nomes,
        index=lista_meses_nomes.index(nome_mes_atual),
    )
    mes_sel = NOME_PARA_NUMERO[mes_selecionado_nome]
with f3:
    busca = st.text_input("Buscar fornecedor/descrição", placeholder="Ex: aluguel, internet...")

f4, f5, f6 = st.columns([1.6, 1.6, 1.2])

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# FILTRO STATUS (SEM EMOJI) — igual seu print
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
STATUS_OPCOES = ["Atrasado", "Recebe em 7 dias", "A receber", "Realizado"]

with f4:
    status_filtro = st.multiselect("Status", options=STATUS_OPCOES)
with f5:
    cats = sorted([c for c in df["Categoria"].dropna().unique().tolist()]) if not df.empty else []
    categoria_sel = st.multiselect("Categoria", options=cats)
with f6:
    ordenar = st.selectbox("Ordenar", options=["Vencimento (próximo)", "Valor (maior)", "Valor (menor)"])

# Aplicação dos Filtros
df_f = pd.DataFrame()
if not df.empty:
    df_f = df[(df["Venc_dt"].dt.year == int(ano_sel)) & (df["Venc_dt"].dt.month == int(mes_sel))].copy()

    if status_filtro:
        df_f = df_f[df_f["Status_Label"].isin(status_filtro)]
    if categoria_sel:
        df_f = df_f[df_f["Categoria"].isin(categoria_sel)]
    if busca.strip():
        df_f = df_f[df_f["Fornecedor_Descricao"].astype(str).str.contains(busca.strip(), case=False, na=False)]

    # Ordenação
    if ordenar == "Valor (maior)":
        df_f = df_f.sort_values("Valor", ascending=False)
    elif ordenar == "Valor (menor)":
        df_f = df_f.sort_values("Valor", ascending=True)
    else:
        df_f = df_f.sort_values("Vencimento", ascending=True)

# -----------------------------
# Resumo
# -----------------------------
st.divider()
st.subheader("Resumo")

if df_f.empty:
    st.info("Nenhum dado encontrado para este período.")
else:
    total_aberto = df_f[df_f["Status_Label"].isin(["A receber", "Recebe em 7 dias"])]["Valor"].sum()
    total_atrasado = df_f[df_f["Status_Label"] == "Atrasado"]["Valor"].sum()
    total_pago = df_f[df_f["Status_Label"] == "Realizado"]["Valor"].sum()
    qtd_7 = df_f[df_f["Status_Label"] == "Recebe em 7 dias"].shape[0]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Total em aberto", fmt_brl(total_aberto), "A vencer + vencendo", "green", icon_svg("calendar"))
    with m2:
        metric_card("Total atrasado", fmt_brl(total_atrasado), "Atenção aos juros" if total_atrasado > 0 else "Tudo certo",
                    "red" if total_atrasado > 0 else "green", icon_svg("alert"))
    with m3:
        metric_card("Total pago", fmt_brl(total_pago), "Neste filtro", "green", icon_svg("check"))
    with m4:
        metric_card("Recebe em 7 dias", str(qtd_7), "Prioridade", "red" if qtd_7 > 0 else "green", icon_svg("calendar"))

# -----------------------------
# Ação Rápida
# -----------------------------
st.divider()
st.subheader("Ação rápida")

if not df_f.empty:
    df_acao = df_f[df_f["Status_BD"] != "Realizado"].copy()
    if df_acao.empty:
        st.info("Todas as contas deste período já foram pagas.")
    else:
        df_acao["venc_fmt"] = pd.to_datetime(df_acao["Vencimento"]).dt.strftime("%d/%m/%Y")
        df_acao["valor_fmt"] = df_acao["Valor"].apply(fmt_brl)

        opcoes = df_acao.apply(lambda r: f"{limpar_txt(r['Fornecedor_Descricao'])} | {r['venc_fmt']} | {r['valor_fmt']}", axis=1).tolist()
        map_id = dict(zip(opcoes, df_acao["id"].tolist()))

        cA1, cA2 = st.columns([3, 1])
        with cA1:
            escolha = st.selectbox("Selecione a conta para baixar:", options=opcoes)

        id_sel = map_id.get(escolha)

        with cA2:
            if st.button("Marcar como pago", type="primary", use_container_width=True):
                if id_sel:
                    conn = conectar()
                    cur = conn.cursor()
                    try:
                        cur.execute("UPDATE transactions SET status='Realizado', data_real=? WHERE id=?",
                                    (date.today(), id_sel))
                        conn.commit()
                        st.success("Conta atualizada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                    finally:
                        conn.close()

# -----------------------------
# Tabela Padronizada (SaaS igual anexo ✅)
# -----------------------------
st.divider()
st.subheader("Detalhamento")

st.markdown("""
<style>
.dt-table table{ width:100%; border-collapse:separate; border-spacing:0; overflow:hidden; border-radius:14px; }
.dt-table thead th{
  text-align:center !important;
  font-weight:800;
  padding:12px 12px;
  border-bottom:1px solid rgba(255,255,255,0.10);
  background:rgba(255,255,255,0.02);
}
.dt-table tbody td{
  padding:12px 12px;
  border-bottom:1px solid rgba(255,255,255,0.06);
  vertical-align:middle;
}
.dt-table tbody tr:hover td{ background:rgba(255,255,255,0.02); }

/* alinhamentos por coluna (Status, Data, Descrição, Categoria, Valor) */
.dt-table tbody td:nth-child(1){ text-align:left; }
.dt-table tbody td:nth-child(2){ text-align:center; }
.dt-table tbody td:nth-child(5){ text-align:right; }
</style>
""", unsafe_allow_html=True)

if not df_f.empty:
    df_view = df_f[["Status_BD", "Vencimento", "Fornecedor_Descricao", "Categoria", "Valor"]].copy()
    df_view.rename(columns={
        "Fornecedor_Descricao": "Descrição",
        "Vencimento": "Data",
        "Status_BD": "Status",
    }, inplace=True)

    df_view["Descrição"] = df_view["Descrição"].apply(limpar_txt)
    df_view["Categoria"] = df_view["Categoria"].apply(limpar_txt)

    df_view["Data"] = pd.to_datetime(df_view["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_view["Valor"] = df_view["Valor"].apply(fmt_brl)

    # atrasado = vencimento < hoje e status_bd != Realizado
    venc_dt = pd.to_datetime(df_f["Vencimento"], errors="coerce").dt.date
    atrasado_mask = (df_f["Status_BD"].astype(str) != "Realizado") & (venc_dt < hoje)

    df_view["Status"] = [
        badge_status_minimal(str(s), bool(a))
        for s, a in zip(df_f["Status_BD"].astype(str).tolist(), atrasado_mask.tolist())
    ]

    st.markdown(f'<div class="dt-table">{df_view.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

    # Exportação (SEM HTML)
    df_export = df_f[["Status_Label", "Vencimento", "Fornecedor_Descricao", "Categoria", "Valor"]].copy()
    df_export.rename(columns={
        "Fornecedor_Descricao": "Descrição",
        "Vencimento": "Data",
        "Status_Label": "Status",
    }, inplace=True)
    df_export["Descrição"] = df_export["Descrição"].apply(limpar_txt)
    df_export["Categoria"] = df_export["Categoria"].apply(limpar_txt)
    df_export["Data"] = pd.to_datetime(df_export["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_export["Valor"] = df_export["Valor"].apply(fmt_brl)
    df_export["Status"] = df_export["Status"].astype(str).str.replace("\n", " ", regex=False).str.strip()

    c_exp1, c_exp2 = st.columns([1, 1])
    with c_exp1:
        csv = df_export.to_csv(index=False, sep=";").encode("utf-8")
        st.download_button(
            "📥 Baixar CSV",
            data=csv,
            file_name=f"contas_pagar_{ano_sel}_{mes_sel}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with c_exp2:
        try:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Contas")
            st.download_button(
                "📥 Baixar Excel",
                data=buffer.getvalue(),
                file_name=f"contas_pagar_{ano_sel}_{mes_sel}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except:
            st.caption("Instale 'openpyxl' para baixar em Excel.")
else:
    st.success("Nenhuma conta encontrada para os filtros selecionados.")
