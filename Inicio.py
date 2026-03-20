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
# CSS — Marca Zonal dark theme
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

footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
header { visibility: hidden; }

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 900px !important;
}

/* Hero card */
.hero-wrap {
    text-align: center;
    padding: 3rem 2rem 2.5rem;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 20px;
    border: 1px solid rgba(14,165,233,0.2);
    margin-bottom: 2.5rem;
}

.hero-title {
    font-family: 'Poppins', sans-serif !important;
    font-size: 2.8rem;
    font-weight: 800;
    color: #e2e8f0;
    margin: 1rem 0 0.5rem;
    letter-spacing: -1px;
}

.hero-sub {
    font-size: 1rem;
    color: #94a3b8;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

.hero-badge {
    display: inline-block;
    background: rgba(14,165,233,0.12);
    border: 1px solid rgba(14,165,233,0.35);
    color: #0ea5e9;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    margin-bottom: 0.5rem;
}

/* Module cards */
.mod-card {
    background: rgba(30,41,59,0.7);
    border: 1px solid rgba(148,163,184,0.1);
    border-radius: 16px;
    padding: 2rem 1.5rem;
    text-align: center;
    transition: border-color 0.2s;
    height: 100%;
}

.mod-card:hover {
    border-color: rgba(14,165,233,0.4);
}

.mod-icon {
    font-size: 2.5rem;
    margin-bottom: 0.8rem;
}

.mod-title {
    font-family: 'Poppins', sans-serif !important;
    font-size: 1.2rem;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 0.5rem;
}

.mod-desc {
    font-size: 0.82rem;
    color: #64748b;
    line-height: 1.6;
}

.mod-tag {
    display: inline-block;
    margin-top: 1rem;
    background: rgba(14,165,233,0.1);
    color: #38bdf8;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 0.2rem 0.7rem;
    border-radius: 12px;
}

/* Visit counter */
.counter-wrap {
    text-align: center;
    padding: 1.2rem;
    background: rgba(30,41,59,0.5);
    border-radius: 12px;
    border: 1px solid rgba(148,163,184,0.08);
    margin-top: 2rem;
}

.counter-num {
    font-family: 'Poppins', sans-serif !important;
    font-size: 2rem;
    font-weight: 800;
    color: #0ea5e9;
}

.counter-label {
    font-size: 0.65rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #475569;
    margin-top: 0.2rem;
}

/* divider */
.mz-divider {
    border: none;
    border-top: 1px solid rgba(148,163,184,0.1);
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Visit counter
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
    f'style="height:90px;margin-bottom:0.5rem;" alt="Marca Zonal">'
    if logo_b64 else ""
)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="hero-wrap">
    {logo_html}
    <div class="hero-title">Marca Zonal</div>
    <div class="hero-sub">Portal de análisis · División Profesional de Paraguay</div>
    <div class="hero-badge">⚽ Apertura 2026</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Module cards
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("""
    <div class="mod-card">
        <div class="mod-icon">📊</div>
        <div class="mod-title">Portal de Jugadores</div>
        <div class="mod-desc">
            Explorá estadísticas individuales, gráficos XY, radares de rendimiento,
            rankings y comparativas de similares para todos los jugadores del torneo.
        </div>
        <div class="mod-tag">Wyscout · Player Stats</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="mod-card">
        <div class="mod-icon">⚽</div>
        <div class="mod-title">Predictor de Partidos</div>
        <div class="mod-desc">
            Modelo Poisson basado en xG, forma reciente y estadísticas de equipo.
            Probabilidades 1X2, marcadores esperados, corners, tarjetas y panel comparativo.
        </div>
        <div class="mod-tag">Poisson · xG · Team Stats</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<p style="text-align:center;color:#475569;font-size:0.78rem;margin-top:1rem;">
    Usá el menú lateral ← para navegar entre secciones
</p>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Visit counter display
# ---------------------------------------------------------------------------
st.markdown('<hr class="mz-divider">', unsafe_allow_html=True)

c1, c2, c3 = st.columns([2, 1, 2])
with c2:
    st.markdown(f"""
    <div class="counter-wrap">
        <div class="counter-num">{_visit_count:,}</div>
        <div class="counter-label">👁️ Visitas totales</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("""
<p style="text-align:center;color:#1e293b;font-size:0.7rem;margin-top:2rem;">
    Marca Zonal · Datos: Wyscout · Apertura 2026
</p>
""", unsafe_allow_html=True)
