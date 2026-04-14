import base64
import os
import sys as _sys

import streamlit as st

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if _ROOT_DIR not in _sys.path:
    _sys.path.insert(0, _ROOT_DIR)

from utils.counter import count_visit


st.set_page_config(
    page_title="Marca Zonal | Portal de Fútbol",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cousine:wght@400;700&family=Poppins:wght@600;700;800&display=swap');

html, body, *, [class*="css"], [class*="st-"],
button, input, select, textarea, label,
.stButton > button, p, span, div {
    font-family: 'Cousine', monospace !important;
}

h1, h2, h3 {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
header { visibility: hidden; }

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 820px !important;
}

.bienvenida-wrap {
    text-align: center;
    padding: 3rem 2rem 2rem;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 20px;
    border: 1px solid rgba(34,197,94,0.2);
    margin-bottom: 2.5rem;
}

.bienvenida-title {
    font-family: 'Poppins', sans-serif !important;
    font-size: 1.6rem;
    font-weight: 800;
    color: #e2e8f0;
    letter-spacing: 1px;
    line-height: 1.3;
    margin: 1.2rem 0 0.6rem;
}

.bienvenida-sub {
    font-size: 0.95rem;
    color: #64748b;
    letter-spacing: 1px;
    margin-bottom: 0.2rem;
}

.stButton > button {
    width: 100%;
    padding: 1.6rem 1rem !important;
    font-family: 'Poppins', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
    background: rgba(30,41,59,0.8) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(148,163,184,0.15) !important;
    border-radius: 14px !important;
    transition: all 0.2s ease !important;
    margin-top: 0.2rem;
}

.stButton > button:hover {
    background: rgba(34,197,94,0.12) !important;
    border-color: rgba(34,197,94,0.45) !important;
    color: #22c55e !important;
    transform: translateY(-2px);
}

.counter-wrap {
    text-align: center;
    padding: 1rem;
    background: rgba(30,41,59,0.4);
    border-radius: 12px;
    border: 1px solid rgba(148,163,184,0.07);
    margin-top: 2rem;
}

.counter-num {
    font-family: 'Poppins', sans-serif !important;
    font-size: 1.8rem;
    font-weight: 800;
    color: #22c55e;
}

.counter-label {
    font-size: 0.62rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #334155;
    margin-top: 0.2rem;
}
</style>
""", unsafe_allow_html=True)

_visit_count = count_visit()

LOGO_PATH = os.path.join(_ROOT_DIR, "assets", "logo_blanco.png")
logo_b64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" '
    f'style="height:100px;margin-bottom:0.2rem;" alt="Marca Zonal">'
    if logo_b64 else '<div style="font-size:3rem;">⚽</div>'
)

st.markdown(f"""
<div class="bienvenida-wrap">
    {logo_html}
    <div class="bienvenida-title">BIENVENIDOS AL PORTAL DE DATOS<br>DE MARCA ZONAL</div>
    <div class="bienvenida-sub">División Profesional de Paraguay · Apertura 2026</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<p style="text-align:center;font-family:'Poppins',sans-serif;font-size:1rem;
          font-weight:700;color:#94a3b8;letter-spacing:1px;margin-bottom:1.2rem;">
    Seleccione qué función le gustaría observar
</p>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    if st.button("ESTADÍSTICAS\nFÚTBOL PARAGUAYO", use_container_width=True):
        st.switch_page("pages/1_📊_Jugadores.py")

with col2:
    if st.button("ÍNDICE DE PROBABILIDADES\nFÚTBOL PARAGUAYO", use_container_width=True):
        st.switch_page("pages/2_⚽_Predictor.py")

with col3:
    if st.button("TIEMPO EFECTIVO\nFÚTBOL PARAGUAYO", use_container_width=True):
        st.switch_page("pages/3_Tiempo_efectivo.py")

st.markdown("---")
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:0.6rem 0.2rem;flex-wrap:wrap;gap:0.5rem;">
    <div style="font-size:0.78rem;color:#64748b;font-family:'Cousine',monospace;">
        👁️ Visitas a la app: <strong style="color:#22c55e;">{_visit_count:,}</strong>
        &nbsp;·&nbsp; Marca Zonal · Apertura 2026
    </div>
    <div style="font-size:0.78rem;color:#64748b;font-family:'Cousine',monospace;">
        𝕏 <a href="https://x.com/marca_zonal" target="_blank"
              style="color:#64748b;text-decoration:none;">@marca_zonal</a>
        &nbsp;·&nbsp;
        📷 <a href="https://instagram.com/marca.zonal" target="_blank"
               style="color:#64748b;text-decoration:none;">@marca.zonal</a>
    </div>
</div>
""", unsafe_allow_html=True)
