import streamlit as st
from textwrap import dedent


def icon_svg(name: str) -> str:
    icons = {
        "trend": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M4 16l6-6 4 4 6-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 8h6v6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
        "wallet": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M3 7.5C3 6.12 4.12 5 5.5 5H19a2 2 0 0 1 2 2v2H7a2 2 0 0 0-2 2v6.5A2.5 2.5 0 0 1 3 17V7.5Z" stroke="currentColor" stroke-width="1.6"/><path d="M7 9h14v8a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2Z" stroke="currentColor" stroke-width="1.6"/><path d="M17 13h2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>""",
        "in": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 20V4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M7 9l5-5 5 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
        "out": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 4v16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M7 15l5 5 5-5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
        "calendar": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M7 3v3M17 3v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M4 8h16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M6 5h12a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" stroke="currentColor" stroke-width="1.6"/></svg>""",
        "check": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M20 6 9 17l-5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
        "alert": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 9v4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M12 17h.01" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M10.3 4.9 3.5 17.2A2 2 0 0 0 5.2 20h13.6a2 2 0 0 0 1.7-2.8L13.7 4.9a2 2 0 0 0-3.4 0Z" stroke="currentColor" stroke-width="1.6"/></svg>""",
        "up": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 4v16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M7 9l5-5 5 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
        "down": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 20V4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M7 15l5 5 5-5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>"""
    }
    return icons.get(name, "")


def metric_card(title: str, value: str, footer_text: str, footer_color: str, icon_html: str = ""):
    color_map = {
        "green": ("rgba(0, 204, 150, 0.12)", "#00CC96", "↑"),
        "red": ("rgba(255, 75, 75, 0.12)", "#FF4B4B", "↓"),
        "gray": ("rgba(108, 117, 125, 0.12)", "#6C757D", "•"),
    }

    bg_footer, border_footer, seta = color_map.get(footer_color, color_map["gray"])

    html = dedent(f"""
    <div class="kpi-card">
        <div style="display:flex;gap:12px;align-items:center;margin-bottom:4px;">
            <div style="width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:rgba(0, 209, 255, 0.1); color:#00D1FF;">
                {icon_html}
            </div>
            <div class="kpi-title">{title}</div>
        </div>

        <div class="kpi-value">{value}</div>

        <div class="kpi-footer" style="background:{bg_footer}; color:{border_footer};">
            <span class="kpi-footer-icon" style="border:1px solid {border_footer};">{seta}</span>
            <span>{footer_text}</span>
        </div>
    </div>
    """).strip()

    st.markdown(html, unsafe_allow_html=True)
