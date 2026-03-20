import streamlit as st
import os
import sys as _sys
import base64

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if _ROOT_DIR not in _sys.path:
    _sys.path.insert(0, _ROOT_DIR)

from utils.counter import count_visit

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Marca Zonal | Portal de Fútbol",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
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

/* Ocultar sidebar y botón de colapso completamente */
[data-testid="stSidebar"]          { display: none !important; }
[data-testid="collapsedControl"]   { display: none !important; }
footer                             { visibility: hidden; }
#MainMenu                          { visibility: hidden; }
header                             { visibility: hidden; }

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 820px !important;
}

/* Bienvenida */
.bienvenida-wrap {
    text-align: center;
    padding: 3rem 2rem 2rem;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 20px;
    border: 1px solid rgba(14,165,233,0.2);
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

/* Botones de navegación */
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
    background: rgba(14,165,233,0.12) !important;
    border-color: rgba(14,165,233,0.45) !important;
    color: #0ea5e9 !important;
    transform: translateY(-2px);
}

/* Contador */
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
    color: #0ea5e9;
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

# ---------------------------------------------------------------------------
# Contador de visitas
# ---------------------------------------------------------------------------
_visit_count = count_visit()

# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Hero — bienvenida
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="bienvenida-wrap">
    {logo_html}
    <div class="bienvenida-title">BIENVENIDOS AL PORTAL DE DATOS<br>DE MARCA ZONAL</div>
    <div class="bienvenida-sub">División Profesional de Paraguay · Apertura 2026</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Selector de función
# ---------------------------------------------------------------------------
st.markdown("""
<p style="text-align:center;font-family:'Poppins',sans-serif;font-size:1rem;
          font-weight:700;color:#94a3b8;letter-spacing:1px;margin-bottom:1.2rem;">
    Seleccione qué función le gustaría observar
</p>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button("📊  Estadísticas de Jugadores\n\nAnálisis individual, radares, XY y rankings", use_container_width=True):
        st.switch_page("pages/1_📊_Jugadores.py")

with col2:
    if st.button("⚽  Predictor de Partidos\n\nProbabilidades, xG, corners y tarjetas", use_container_width=True):
        st.switch_page("pages/2_⚽_Predictor.py")

# ---------------------------------------------------------------------------
# Contador
# ---------------------------------------------------------------------------
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
_, cc, _ = st.columns([2, 1, 2])
with cc:
    st.markdown(f"""
    <div class="counter-wrap">
        <div class="counter-num">{_visit_count:,}</div>
        <div class="counter-label">👁 Visitas totales</div>
    </div>
    """, unsafe_allow_html=True)
