import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import io
import os
import json
import urllib.request
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as _fm
from collections import defaultdict
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from utils.data_processing import load_and_process_data
from utils.xy_chart import create_xy_chart
from utils.bar_chart import create_bar_chart
from utils.pizza_chart import create_pizza_chart
from utils.translations import translate
import sys as _sys
_PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_PAGE_DIR)
if _ROOT_DIR not in _sys.path:
    _sys.path.insert(0, _ROOT_DIR)

# Logo paths
_APP_DIR = _ROOT_DIR
LOGO_NEGRO = os.path.join(_APP_DIR, 'assets', 'logo_negro.png')
LOGO_BLANCO = os.path.join(_APP_DIR, 'assets', 'logo_blanco.png')

# ---------------------------------------------------------------------------
# Fuente Cousine — descarga y registra automáticamente si no está disponible
# ---------------------------------------------------------------------------
def _setup_cousine_font():
    """Registra la fuente Cousine en matplotlib.
    Primero busca en assets/fonts/, luego intenta descargarla de Google Fonts."""
    already = [f.name for f in _fm.fontManager.ttflist]
    if 'Cousine' in already:
        return 'Cousine'

    font_dir = os.path.join(_APP_DIR, 'assets', 'fonts')
    os.makedirs(font_dir, exist_ok=True)

    _cousine_files = {
        'Cousine-Regular.ttf': (
            'https://github.com/google/fonts/raw/main/apache/cousine/Cousine-Regular.ttf'
        ),
        'Cousine-Bold.ttf': (
            'https://github.com/google/fonts/raw/main/apache/cousine/Cousine-Bold.ttf'
        ),
    }
    registered = False
    for fname, url in _cousine_files.items():
        fpath = os.path.join(font_dir, fname)
        if not os.path.exists(fpath):
            try:
                urllib.request.urlretrieve(url, fpath)
            except Exception:
                continue
        if os.path.exists(fpath):
            _fm.fontManager.addfont(fpath)
            registered = True

    return 'Cousine' if registered else 'DejaVu Sans'

_CHART_FONT = _setup_cousine_font()
matplotlib.rcParams['font.family'] = _CHART_FONT
matplotlib.rcParams['font.sans-serif'] = [_CHART_FONT, 'DejaVu Sans', 'Arial']

# ---------------------------------------------------------------------------
# Bar chart metrics — 4 categories for the comparison chart
# ---------------------------------------------------------------------------
BAR_METRICS = {
    'Defensa': [
        'Defensive duels won, %',
        'Aerial duels won, %',
        'Shots blocked per 90',
        'Interceptions per 90',
    ],
    'Ataque': [
        'Goals per 90',
        'Shots on target per 90',
        'Assists per 90',
        'Offensive duels won, %',
    ],
    'Posesión': [
        'Received passes per 90',
        'Dribbles won per 90',
        'Touches in box per 90',
        'Progressive runs per 90',
    ],
    'Distribución': [
        'Accurate passes per 90',
        'Shot assists per 90',
        'Accurate passes to final third per 90',
        'Accurate progressive passes per 90',
    ],
}

# ---------------------------------------------------------------------------
# Pizza chart metrics — 3 categories × 5 metrics for the radial chart
# ---------------------------------------------------------------------------
PIZZA_METRICS = {
    'Defensa': [
        'Defensive duels won, %',
        'Aerial duels won, %',
        'Shots blocked per 90',
        'Interceptions per 90',
        'Fouls per 90',
    ],
    'Ataque': [
        'Goals per 90',
        'Shots on target per 90',
        'Assists per 90',
        'Dribbles won per 90',
        'Progressive runs per 90',
    ],
    'Distribución': [
        'Received passes per 90',
        'Accurate passes per 90',
        'Key passes per 90',
        'Accurate passes to final third per 90',
        'Accurate progressive passes per 90',
    ],
}

# Columns excluded from metric selectors and table display
NON_METRIC_COLS = {
    'Player', 'Team', 'Team within selected timeframe', 'Position',
    'Position Group', 'Market value', 'Contract expires',
    'Passport country', 'On loan', 'Birth country', 'Foot', 'Height', 'Weight',
}

# Columns to always hide from the table
HIDDEN_TABLE_COLS = {
    'Position', 'Position Group', 'Contract expires', 'Market value',
    'Team within selected timeframe', 'Passport country', 'On loan',
    # Excluidas del pentágono y tabla: penales tienen mucho ruido (0 cuando no hay intentos)
    'Penalty conversion, %',
    'Direct free kicks on target, %',
}

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Contador de visitas compartido
# ---------------------------------------------------------------------------
from utils.counter import count_visit
_visit_count = count_visit()


st.set_page_config(page_title="Jugadores | Marca Zonal", layout="wide")

# Professional theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cousine:wght@400;700&family=Poppins:wght@600;700&display=swap');

html, body, *, [class*="css"], [class*="st-"],
button, input, select, textarea, label,
.stButton > button, .stSelectbox div, .stRadio div,
.stSlider div, .stTextInput input, .stNumberInput input,
.stDataFrame, .stTable, p, span, div {
    font-family: 'Cousine', monospace !important;
}

h1, h2, h3 {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 700 !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.12), rgba(22, 163, 74, 0.04));
    border: 1px solid rgba(34, 197, 94, 0.2);
    border-radius: 12px;
    padding: 14px 18px;
}

[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    opacity: 0.7;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background-color: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    padding: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 500;
}

/* Labels */
.stSelectbox label, .stRadio label, .stSlider label {
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.3px;
}

/* Expanders */
.streamlit-expanderHeader {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
}

/* Download buttons */
.stDownloadButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

/* Ocultar sidebar completamente */
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# Botón volver al inicio
if st.button("← Volver al inicio"):
    st.switch_page("app.py")

st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    df = load_and_process_data()
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# Drop rows without position group
df = df.dropna(subset=['Position Group'])

# Identify metric columns (numeric only, excluding non-metric cols)
metric_columns = sorted([
    c for c in df.columns
    if c not in NON_METRIC_COLS and pd.api.types.is_numeric_dtype(df[c])
])

# ---------------------------------------------------------------------------
# Metric categorization for organized display
# ---------------------------------------------------------------------------
def categorize_metric(col_name):
    """Group a metric into a display category (outfield players)."""
    cl = col_name.lower()
    if 'shots blocked' in cl:
        return '\U0001f6e1\ufe0f Defensa'
    if 'fouls suffered' in cl:
        return '\u26a1 Posesi\u00f3n'
    if 'received' in cl:
        return '\u26a1 Posesi\u00f3n'
    if 'assist' in cl or cl.startswith('xa'):
        return '\U0001f3af Creaci\u00f3n'
    # Early checks: evita que 'goalie' matchee 'goal' y 'penalty area' matchee 'penalty'
    if 'goalie box' in cl:
        return '\u2197\ufe0f Centros'
    if 'penalty area' in cl:
        return '\U0001f4d0 Pases'
    if any(k in cl for k in ['goal', 'shot', 'xg', 'conversion']):
        return '\u26bd Goles y Remates'
    if 'cross' in cl or 'flank' in cl:
        return '\u2197\ufe0f Centros'
    if any(k in cl for k in ['pass', 'smart', 'through', 'key', 'deep']):
        return '\U0001f4d0 Pases'
    if 'duel' in cl or 'aerial' in cl:
        return '\U0001f4aa Duelos'
    if any(k in cl for k in ['defensive', 'sliding', 'intercept', 'cbit']):
        return '\U0001f6e1\ufe0f Defensa'
    if any(k in cl for k in ['dribble', 'touch', 'progressive', 'acceleration', 'offensive', 'attacking']):
        return '\u26a1 Posesi\u00f3n'
    if any(k in cl for k in ['foul', 'card', 'yellow', 'red']):
        return '\U0001f4cb Disciplina'
    if any(k in cl for k in ['corner', 'free kick']):
        return '\U0001f945 Pelota Parada'
    return '\U0001f4ca Otros'


def categorize_metric_gk(col_name):
    """Group a metric into a display category for goalkeepers."""
    cl = col_name.lower()
    # Portería — métricas bajo palos (va primero para evitar conflictos)
    if any(k in cl for k in ['conceded', 'xg against', 'prevented', 'shots against',
                               'clean sheet', 'save rate', 'exits']):
        return '\U0001f945 Porter\u00eda'
    # Distribución — métricas de pase/salida con balón
    if any(k in cl for k in ['long pass', 'average pass', 'average long', 'progressive pass',
                               'forward pass', 'final third', 'pass length']):
        return '\U0001f4d0 Distribuci\u00f3n'
    if any(k in cl for k in ['short / medium pass', 'accurate pass', 'pass per 90',
                               'lateral pass', 'back pass', 'accurate back', 'accurate lateral',
                               'accurate short', 'accurate forward']):
        return '\U0001f4d0 Distribuci\u00f3n'
    # Recepción — balones recibidos
    if 'received' in cl:
        return '\U0001f4e5 Recepci\u00f3n'
    # Duelos aéreos y generales
    if 'aerial' in cl:
        return '\U0001f4aa Duelos A\u00e9reos'
    if 'duel' in cl:
        return '\U0001f4aa Duelos A\u00e9reos'
    # Acciones defensivas
    if any(k in cl for k in ['defensive', 'sliding', 'intercept', 'shots blocked', 'cbit',
                               'successful defensive']):
        return '\U0001f6e1\ufe0f Acciones Def.'
    # Disciplina
    if any(k in cl for k in ['foul', 'card', 'yellow', 'red']):
        return '\U0001f4cb Disciplina'
    return '\U0001f4ca Otros'


CATEGORY_ORDER = [
    '\u26bd Goles y Remates', '\U0001f3af Creaci\u00f3n', '\U0001f4d0 Pases',
    '\u2197\ufe0f Centros', '\u26a1 Posesi\u00f3n', '\U0001f4aa Duelos',
    '\U0001f6e1\ufe0f Defensa', '\U0001f4e5 Recepci\u00f3n',
    '\U0001f4cb Disciplina',
]

GK_CATEGORY_ORDER = [
    '\U0001f945 Porter\u00eda',
    '\U0001f4d0 Distribuci\u00f3n',
    '\U0001f4aa Duelos A\u00e9reos',
    '\U0001f4e5 Recepci\u00f3n',
    '\U0001f4cb Disciplina',
]

# ---------------------------------------------------------------------------
# Métricas curadas — compartidas entre Tab 1 (barras) y Tab 3 (pentágono)
# ---------------------------------------------------------------------------
# Métricas per 90 que deben aparecer siempre aunque no cumplan el filtro general
_ALWAYS_COLS = {
    'Goals per 90',
    'Shots on target per 90',
    'Successful attacking actions per 90',
    'Successful defensive actions per 90',
    'Received passes per 90',
    'Received long passes per 90',
}

# Columnas GK curadas: portería, distribución, duelos aéreos, acciones defensivas
_GK_DISPLAY_COLS = [
    # Portería — solo métricas por 90 y % (comparables entre porteros con distinto tiempo)
    'Conceded goals per 90',
    'xG against per 90',
    'Prevented goals per 90',
    'Shots against per 90',
    'Save rate, %',
    'Exits per 90',
    # Distribución — porcentajes de precisión
    'Accurate passes, %',
    'Accurate forward passes, %',
    'Accurate back passes, %',
    'Accurate lateral passes, %',
    'Accurate short / medium passes, %',
    'Accurate long passes, %',
    'Accurate smart passes, %',
    'Accurate passes to final third, %',
    'Accurate passes to penalty area, %',
    'Accurate through passes, %',
    'Accurate progressive passes, %',
    # Distribución — volumen preciso por 90 (calculado: totales precisos / minutos * 90)
    'Accurate passes per 90',
    'Accurate forward passes per 90',
    'Accurate back passes per 90',
    'Accurate lateral passes per 90',
    'Accurate short / medium passes per 90',
    'Accurate long passes per 90',
    'Accurate smart passes per 90',
    'Accurate passes to final third per 90',
    'Accurate passes to penalty area per 90',
    'Accurate through passes per 90',
    'Accurate progressive passes per 90',
    # Promedios de longitud
    'Average pass length, m',
    'Average long pass length, m',
    # Recepción
    'Received passes per 90',
    # Duelos aéreos
    'Aerial duels per 90',
    'Aerial duels won, %',
    # Disciplina
    'Yellow cards per 90',
]


def _get_display_cols(df):
    """Devuelve las columnas curadas para barras de percentiles y pentágono OVERALL.
    Solo métricas de calidad: %, Accurate, won y categorías completas.
    Excluye porteros — usar _get_display_cols_gk() para ellos."""
    return [
        c for c in df.columns
        if (c.endswith(' per 90') or c.endswith(', %'))
        and c not in NON_METRIC_COLS
        and c not in HIDDEN_TABLE_COLS
        and pd.api.types.is_numeric_dtype(df[c])
        and (
            c.endswith(', %') or
            'Accurate' in c or
            'won' in c.lower() or
            categorize_metric(c) in {
                '\U0001f4cb Disciplina',
                '\U0001f3af Creaci\u00f3n',
                '\U0001f6e1\ufe0f Defensa',
            } or
            c in _ALWAYS_COLS
        )
    ]


def _get_display_cols_gk(df):
    """Devuelve las columnas curadas para porteros."""
    return [c for c in _GK_DISPLAY_COLS if c in df.columns
            and pd.api.types.is_numeric_dtype(df[c])]


# Métricas GK donde menor valor = mejor rendimiento → percentil invertido
_GK_LOWER_IS_BETTER = {'Conceded goals', 'Conceded goals per 90'}

# Métricas exclusivas de portero — solo visibles en XY cuando se selecciona Portero
_GK_ONLY_METRICS = {
    'Conceded goals per 90',
    'xG against per 90',
    'Prevented goals per 90',
    'Shots against per 90',
    'Exits per 90',
    'Back passes received as GK per 90',
}


# ---------------------------------------------------------------------------
# Header / portada
# ---------------------------------------------------------------------------
_team_col_hdr = 'Team within selected timeframe' if 'Team within selected timeframe' in df.columns else 'Team'
_n_players = len(df)
_n_teams   = int(df[_team_col_hdr].nunique())
_n_metrics = len(metric_columns)

# Logo centrado
_hdr_l, _hdr_c, _hdr_r = st.columns([1, 2, 1])
with _hdr_c:
    st.image(LOGO_BLANCO, use_column_width=True)

st.markdown(f"""
<div style="text-align:center; padding: 4px 0 28px 0;">

  <p style="
    font-size: 2.1rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 6px 0;
    font-family: 'Poppins', sans-serif;
    letter-spacing: 3px;
    text-transform: uppercase;
  ">Portal de Datos</p>

  <p style="
    font-size: 1.05rem;
    color: #9ca3af;
    margin: 0 0 24px 0;
    letter-spacing: 1px;
  ">Análisis de rendimiento del fútbol paraguayo · Apertura 2026</p>

  <div style="
    display: inline-flex;
    gap: 48px;
    background: #1a1f2e;
    border: 1px solid #2d3748;
    border-radius: 14px;
    padding: 16px 40px;
  ">
    <div style="text-align:center;">
      <div style="font-size:2rem; font-weight:700; color:#22c55e; line-height:1;">{_n_players}</div>
      <div style="color:#6b7280; font-size:0.78rem; margin-top:4px; letter-spacing:1px; text-transform:uppercase;">Jugadores</div>
    </div>
    <div style="width:1px; background:#2d3748;"></div>
    <div style="text-align:center;">
      <div style="font-size:2rem; font-weight:700; color:#22c55e; line-height:1;">{_n_teams}</div>
      <div style="color:#6b7280; font-size:0.78rem; margin-top:4px; letter-spacing:1px; text-transform:uppercase;">Equipos</div>
    </div>
    <div style="width:1px; background:#2d3748;"></div>
    <div style="text-align:center;">
      <div style="font-size:2rem; font-weight:700; color:#22c55e; line-height:1;">{_n_metrics}</div>
      <div style="color:#6b7280; font-size:0.78rem; margin-top:4px; letter-spacing:1px; text-transform:uppercase;">Métricas</div>
    </div>
  </div>

</div>
<hr style="border:none; border-top:1px solid #2d3748; margin:0 0 12px 0;">
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Campo de juego — mapa de posiciones
# ---------------------------------------------------------------------------

# Coordenadas (x%, y%) sobre el campo SVG.
# y=0 → arco rival (ataque) · y=100 → arco propio (defensa)
_POS_XY = {
    'GK':   (50, 88),
    'LCB':  (32, 78),  'RCB':  (68, 78),
    'LB':   (13, 68),  'RB':   (87, 68),
    'LWB':  ( 8, 58),  'RWB':  (92, 58),
    'LDMF': (34, 52),  'RDMF': (66, 52),  'DMF': (50, 52),
    'LCMF': (32, 42),  'RCMF': (68, 42),
    'LAMF': (26, 32),  'RAMF': (74, 32),  'AMF': (50, 30),
    'LW':   (11, 22),  'RW':   (89, 22),
    'LWF':  (15, 18),  'RWF':  (85, 18),
    'CF':   (50, 14),
}


def _field_html(position_code: str) -> str:
    """Genera un SVG de campo táctico (fondo oscuro, líneas blancas) con
    el punto de posición del jugador marcado en sky-blue."""
    W, H = 120, 168          # píxeles del SVG
    M = 6                    # margen exterior
    fw = W - 2 * M           # ancho campo = 108
    fh = H - 2 * M           # alto campo  = 156

    def fx(xp): return M + xp / 100 * fw   # % → px X
    def fy(yp): return M + yp / 100 * fh   # % → px Y

    # Coordenadas del jugador
    px, py = _POS_XY.get(position_code, (50, 50))
    dot_x, dot_y = fx(px), fy(py)

    # Colores del tema oscuro
    bg      = '#0f172a'
    line_c  = 'rgba(255,255,255,0.55)'
    dot_c   = '#0ea5e9'
    dot_rim = '#ffffff'

    # Áreas (en %)
    pa_w = 55   # ancho área penal (% del campo)
    pa_h_pct = 22   # alto área penal (% del campo)
    ga_w = 32   # ancho área chica
    ga_h_pct = 10
    # Goal (poste)
    goal_w = 22
    goal_h_pct = 4

    # px equivalentes
    pa_left  = fx(50 - pa_w / 2)
    pa_right = fx(50 + pa_w / 2)
    pa_h     = fh * pa_h_pct / 100

    ga_left  = fx(50 - ga_w / 2)
    ga_right = fx(50 + ga_w / 2)
    ga_h     = fh * ga_h_pct / 100

    goal_left  = fx(50 - goal_w / 2)
    goal_right = fx(50 + goal_w / 2)
    goal_h     = fh * goal_h_pct / 100

    cy_center = fy(50)
    r_circle  = fw * 0.155

    lines = f"""
    <svg xmlns="http://www.w3.org/2000/svg"
         width="{W}" height="{H}"
         viewBox="0 0 {W} {H}">

      <!-- Fondo del campo -->
      <rect width="{W}" height="{H}" fill="{bg}" rx="6"/>

      <!-- Borde campo -->
      <rect x="{M}" y="{M}" width="{fw}" height="{fh}"
            fill="none" stroke="{line_c}" stroke-width="1.2" rx="2"/>

      <!-- Línea de centro -->
      <line x1="{M}" y1="{cy_center}" x2="{M+fw}" y2="{cy_center}"
            stroke="{line_c}" stroke-width="0.9"/>

      <!-- Círculo central -->
      <circle cx="{fx(50)}" cy="{cy_center}" r="{r_circle}"
              fill="none" stroke="{line_c}" stroke-width="0.9"/>
      <circle cx="{fx(50)}" cy="{cy_center}" r="1.8"
              fill="{line_c}"/>

      <!-- Área penal arriba -->
      <rect x="{pa_left}" y="{M}" width="{pa_right-pa_left}" height="{pa_h}"
            fill="none" stroke="{line_c}" stroke-width="0.9"/>
      <!-- Área chica arriba -->
      <rect x="{ga_left}" y="{M}" width="{ga_right-ga_left}" height="{ga_h}"
            fill="none" stroke="{line_c}" stroke-width="0.9"/>
      <!-- Portería arriba -->
      <rect x="{goal_left}" y="{M - goal_h}" width="{goal_right-goal_left}" height="{goal_h}"
            fill="none" stroke="{line_c}" stroke-width="1.2"/>

      <!-- Área penal abajo -->
      <rect x="{pa_left}" y="{M+fh-pa_h}" width="{pa_right-pa_left}" height="{pa_h}"
            fill="none" stroke="{line_c}" stroke-width="0.9"/>
      <!-- Área chica abajo -->
      <rect x="{ga_left}" y="{M+fh-ga_h}" width="{ga_right-ga_left}" height="{ga_h}"
            fill="none" stroke="{line_c}" stroke-width="0.9"/>
      <!-- Portería abajo -->
      <rect x="{goal_left}" y="{M+fh}" width="{goal_right-goal_left}" height="{goal_h}"
            fill="none" stroke="{line_c}" stroke-width="1.2"/>

      <!-- Punto de penalty arriba -->
      <circle cx="{fx(50)}" cy="{fy(14)}" r="1.5" fill="{line_c}"/>
      <!-- Punto de penalty abajo -->
      <circle cx="{fx(50)}" cy="{fy(86)}" r="1.5" fill="{line_c}"/>

      <!-- Posición del jugador -->
      <circle cx="{dot_x:.1f}" cy="{dot_y:.1f}" r="7"
              fill="{dot_c}" stroke="{dot_rim}" stroke-width="1.5" opacity="0.92"/>
      <text x="{dot_x:.1f}" y="{dot_y + 1:.1f}"
            text-anchor="middle" dominant-baseline="middle"
            font-family="Cousine,monospace" font-size="5.5" font-weight="700"
            fill="#ffffff">{position_code}</text>
    </svg>"""
    return lines


def _player_header_html(player_name, position_code, pos_group,
                         team, age, matches, minutes) -> str:
    """Tarjeta completa: campo a la izquierda, nombre + stats a la derecha."""
    field_svg = _field_html(position_code)
    age_str     = str(int(age))     if age     and str(age)     != 'nan' else '—'
    matches_str = str(int(matches)) if matches and str(matches) != 'nan' else '—'
    minutes_str = str(int(minutes)) if minutes and str(minutes) != 'nan' else '—'

    return f"""
<link href="https://fonts.googleapis.com/css2?family=Cousine:wght@400;700&family=Poppins:wght@600;700&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:transparent;font-family:'Cousine',monospace}}
  .card{{
    display:flex;align-items:center;gap:20px;
    padding:14px 18px;
    background:rgba(30,41,59,0.55);
    border:1px solid rgba(148,163,184,0.13);
    border-radius:14px;
  }}
  .field-wrap{{flex-shrink:0}}
  .info{{flex:1;min-width:0}}
  .pname{{
    font-family:'Poppins',sans-serif;font-size:1.35rem;
    font-weight:700;color:#e2e8f0;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
    margin-bottom:5px;
  }}
  .pbadge{{
    display:inline-block;
    background:rgba(14,165,233,0.14);
    border:1px solid rgba(14,165,233,0.38);
    color:#38bdf8;font-size:0.68rem;font-weight:700;
    letter-spacing:1.5px;text-transform:uppercase;
    padding:2px 9px;border-radius:20px;margin-bottom:13px;
  }}
  .sgrid{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
  .sitem{{
    background:rgba(15,23,42,0.55);
    border:1px solid rgba(148,163,184,0.09);
    border-radius:9px;padding:8px 12px;
  }}
  .slabel{{
    font-size:0.6rem;letter-spacing:1.5px;
    text-transform:uppercase;color:#475569;margin-bottom:3px;
  }}
  .sval{{
    font-family:'Poppins',sans-serif;font-size:1rem;
    font-weight:700;color:#e2e8f0;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  }}
</style>
<div class="card">
  <div class="field-wrap">{field_svg}</div>
  <div class="info">
    <div class="pname">{player_name}</div>
    <div class="pbadge">{position_code} &nbsp;·&nbsp; {pos_group}</div>
    <div class="sgrid">
      <div class="sitem"><div class="slabel">Club</div>
        <div class="sval" title="{team}">{team}</div></div>
      <div class="sitem"><div class="slabel">Edad</div>
        <div class="sval">{age_str}</div></div>
      <div class="sitem"><div class="slabel">Partidos</div>
        <div class="sval">{matches_str}</div></div>
      <div class="sitem"><div class="slabel">Minutos</div>
        <div class="sval">{minutes_str}</div></div>
    </div>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_table, tab_xy, tab_bar, tab_pizza, tab_similar, tab_ranking = st.tabs(
    ["📊 Tabla de datos", "📈 Gráfico XY", "🏆 OVERALL", "🎯 Radial", "🔍 Similares", "🏅 Rankings"]
)

# ---- Tab 1: Data Table ---------------------------------------------------

# Color map per metric category
CATEGORY_COLORS = {
    '\U0001f6e1\ufe0f Defensa':      '#f97316',   # naranja
    '\U0001f4aa Duelos':             '#fb923c',   # naranja claro
    '\u26a1 Posesi\u00f3n':          '#22c55e',   # verde
    '\u26bd Goles y Remates':        '#ef4444',   # rojo
    '\U0001f3af Creaci\u00f3n':      '#a78bfa',   # violeta
    '\u2197\ufe0f Centros':          '#60a5fa',   # azul claro
    '\U0001f4d0 Pases':              '#0ea5e9',   # sky blue
    '\U0001f4e5 Recepci\u00f3n':     '#38bdf8',   # sky claro
    '\U0001f4cb Disciplina':         '#6b7280',   # gris
    '\U0001f945 Pelota Parada':      '#f59e0b',   # amber
}

# Colores para categorías de portero
GK_CATEGORY_COLORS = {
    '\U0001f945 Porter\u00eda':       '#10b981',   # emerald verde
    '\U0001f4d0 Distribuci\u00f3n':  '#0ea5e9',   # sky blue
    '\U0001f4aa Duelos A\u00e9reos': '#a78bfa',   # violeta
    '\U0001f4e5 Recepci\u00f3n':     '#38bdf8',   # sky claro
    '\U0001f4cb Disciplina':         '#6b7280',   # gris
}


def _compute_percentile(player_val, series):
    """Return 0-99 percentile of player_val within series.
    Si el valor del jugador es 0, retorna 0 directamente para evitar
    percentiles inflados por empate en cero."""
    if player_val == 0.0:
        return 0
    vals = pd.to_numeric(series, errors='coerce').dropna()
    if len(vals) == 0:
        return 0
    return int(np.sum(vals <= player_val) / len(vals) * 99)


def _render_all_bars(categorized, category_order, category_colors):
    """Render all metric categories as BallerzBantz-style bars via components.html."""
    total_rows = sum(len(categorized[cat]) for cat in category_order if cat in categorized)
    n_cats     = sum(1 for cat in category_order if cat in categorized)
    height     = total_rows * 38 + n_cats * 52 + 60

    css = """
    <style>
      * { box-sizing: border-box; margin: 0; padding: 0; }
      body {
        font-family: 'Cousine', monospace;
        background: #0e1117;
        color: #b0b8c8;
        padding: 4px 2px;
      }
      .legend {
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 8px; padding-bottom: 5px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
      }
      .legend-name { width:195px; font-size:11px; color:#555; text-align:right; flex-shrink:0; }
      .legend-bar  { flex:1; font-size:11px; color:#555; padding-left:8px; }
      .legend-pct  { width:36px; font-size:11px; color:#555; text-align:center; flex-shrink:0; }
      .cat-block   { margin-bottom: 20px; }
      .cat-header  {
        font-family: 'Poppins', 'Cousine', monospace;
        font-weight: 700; font-size: 12px;
        text-transform: uppercase; letter-spacing: 1.2px;
        margin-bottom: 8px; padding-bottom: 5px;
      }
      .metric-row  { display:flex; align-items:center; gap:10px; margin:4px 0; }
      .metric-name {
        width: 195px; font-size: 12.5px; color: #b0b8c8;
        text-align: right; flex-shrink: 0; line-height: 1.3;
      }
      .bar-container {
        flex: 1; background: rgba(255,255,255,0.07);
        border-radius: 5px; height: 28px;
        position: relative; overflow: hidden;
      }
      .bar-fill {
        height: 100%; border-radius: 5px;
        display: flex; align-items: center; padding-left: 8px;
      }
      .bar-value  { color:#fff; font-size:12px; font-weight:700; white-space:nowrap; }
      .pct-num    { width:36px; font-size:15px; font-weight:800; text-align:center; flex-shrink:0; }
    </style>
    """

    body = """
    <div class="legend">
      <div class="legend-name">Métrica</div>
      <div class="legend-bar">Valor &nbsp;&nbsp;(barra = percentil)</div>
      <div class="legend-pct">%il</div>
    </div>
    """

    for cat in category_order:
        if cat not in categorized:
            continue
        color = category_colors.get(cat, '#94a3b8')
        body += f'<div class="cat-block">'
        body += (f'<div class="cat-header" '
                 f'style="color:{color}; border-bottom:2px solid {color}40;">'
                 f'{cat}</div>')
        for m in categorized[cat]:
            bw = max(int(m["pct"]), 3)
            body += (
                f'<div class="metric-row">'
                f'<div class="metric-name">{m["metric"]}</div>'
                f'<div class="bar-container">'
                f'<div class="bar-fill" style="width:{bw}%; background:{color}cc;">'
                f'<span class="bar-value">{m["value"]}</span>'
                f'</div></div>'
                f'<div class="pct-num" style="color:{color};">{m["pct"]}</div>'
                f'</div>'
            )
        body += '</div>'

    full_html = f'<!DOCTYPE html><html><head>{css}</head><body>{body}</body></html>'
    components.html(full_html, height=height, scrolling=True)


# ---------------------------------------------------------------------------
# Pentagon chart helpers (Tab 3)
# ---------------------------------------------------------------------------

# Mapeo de macro-categorías del pentágono a categorías internas
PENTAGON_GROUPS = {
    'ATQ': ['\u26bd Goles y Remates'],
    'POS': ['\u26a1 Posesi\u00f3n'],
    'PAS': ['\U0001f4d0 Pases', '\u2197\ufe0f Centros'],
    'CRE': ['\U0001f3af Creaci\u00f3n'],
    'DEF': ['\U0001f6e1\ufe0f Defensa', '\U0001f4aa Duelos'],  # con penalización por Disciplina
}
PENTAGON_LABELS_ES = {
    'ATQ': 'Ataque',
    'POS': 'Posesión',
    'PAS': 'Pases',
    'CRE': 'Creatividad',
    'DEF': 'Defensa',
}

# Pentágono GK — 5 ejes con datos disponibles en el dataset
GK_PENTAGON_GROUPS = {
    'DIST': ['\U0001f4d0 Distribuci\u00f3n'],
    'DUE':  ['\U0001f4aa Duelos A\u00e9reos'],
    'DEF':  ['\U0001f6e1\ufe0f Acciones Def.'],
    'REC':  ['\U0001f4e5 Recepci\u00f3n'],
    'JUE':  ['\U0001f4d0 Distribuci\u00f3n', '\U0001f4e5 Recepci\u00f3n'],  # juego con balón global
}
GK_PENTAGON_LABELS_ES = {
    'DIST': 'Distribución',
    'DUE':  'Duelos',
    'DEF':  'Acciones Def.',
    'REC':  'Recepción',
    'JUE':  'Juego',
}


def _compute_pentagon_scores(player_data, comparison_df, all_cols):
    """Calcula los 5 puntajes del pentágono promediando percentiles por macro-categoría."""
    pcts_by_cat = defaultdict(list)
    for c in all_cols:
        val = player_data.get(c, None)
        if pd.isnull(val):
            continue
        pv = float(val)
        pct = _compute_percentile(pv, comparison_df[c]) if c in comparison_df.columns else 0
        cat = categorize_metric(c)
        pcts_by_cat[cat].append(pct)

    def avg_cats(*cats):
        vals = []
        for cat in cats:
            vals.extend(pcts_by_cat.get(cat, []))
        return float(np.mean(vals)) if vals else 0.0

    atq = avg_cats('\u26bd Goles y Remates')
    pos = avg_cats('\u26a1 Posesi\u00f3n')
    pas = avg_cats('\U0001f4d0 Pases', '\u2197\ufe0f Centros')
    cre = avg_cats('\U0001f3af Creaci\u00f3n')
    def_pos = avg_cats('\U0001f6e1\ufe0f Defensa', '\U0001f4aa Duelos')
    def_neg = avg_cats('\U0001f4cb Disciplina')
    def_score = float(np.clip(def_pos - def_neg * 0.25, 0, 99))

    return {
        'ATQ': int(round(atq)),
        'POS': int(round(pos)),
        'PAS': int(round(pas)),
        'CRE': int(round(cre)),
        'DEF': int(round(def_score)),
    }


def _compute_avg_pentagon_scores(comparison_df, all_cols):
    """Calcula el puntaje promedio del pentágono para todo el pool de comparación.
    Para cada métrica calcula el percentil de cada jugador y promedia por categoría."""
    avg_pcts_by_cat = defaultdict(list)

    for c in all_cols:
        if c not in comparison_df.columns:
            continue
        cat = categorize_metric(c)
        col_vals = pd.to_numeric(comparison_df[c], errors='coerce').dropna()
        if len(col_vals) == 0:
            continue
        # Percentil de cada jugador del pool en esta métrica
        pcts = [0 if v == 0.0 else int(np.sum(col_vals <= v) / len(col_vals) * 99)
                for v in col_vals]
        avg_pcts_by_cat[cat].append(float(np.mean(pcts)))

    def avg_cats(*cats):
        vals = []
        for cat in cats:
            vals.extend(avg_pcts_by_cat.get(cat, []))
        return float(np.mean(vals)) if vals else 0.0

    atq     = avg_cats('\u26bd Goles y Remates')
    pos     = avg_cats('\u26a1 Posesi\u00f3n')
    pas     = avg_cats('\U0001f4d0 Pases', '\u2197\ufe0f Centros')
    cre     = avg_cats('\U0001f3af Creaci\u00f3n')
    def_pos = avg_cats('\U0001f6e1\ufe0f Defensa', '\U0001f4aa Duelos')
    def_neg = avg_cats('\U0001f4cb Disciplina')
    def_score = float(np.clip(def_pos - def_neg * 0.25, 0, 99))

    return {
        'ATQ': int(round(atq)),
        'POS': int(round(pos)),
        'PAS': int(round(pas)),
        'CRE': int(round(cre)),
        'DEF': int(round(def_score)),
    }


# ── Columnas explícitas por eje del pentágono GK ─────────────────────────────
_GK_PENTAGON_COLS = {
    'REF': [
        'Shots against per 90',
        'Save rate, %',
    ],
    'EFE': [
        'Conceded goals per 90',   # invertido: menor = mejor
        'xG against per 90',       # invertido: menor = mejor
        'Prevented goals per 90',
    ],
    'DIS': [
        'Accurate passes per 90',
        'Accurate forward passes per 90',
        'Accurate lateral passes per 90',
        'Accurate short / medium passes per 90',
        'Accurate long passes per 90',
        'Accurate passes, %',
        'Accurate forward passes, %',
        'Accurate lateral passes, %',
        'Accurate short / medium passes, %',
        'Accurate long passes, %',
    ],
    'DISP': [
        'Accurate passes to final third per 90',
        'Accurate passes to penalty area per 90',
        'Accurate progressive passes per 90',
        'Accurate passes to final third, %',
        'Accurate passes to penalty area, %',
        'Accurate progressive passes, %',
    ],
    'ALCP': [
        'Average pass length, m',
        'Average long pass length, m',
    ],
}

# Columnas donde percentil MENOR es MEJOR (se invierte)
_GK_LOWER_IS_BETTER_PENT = {'Conceded goals per 90', 'xG against per 90'}


def _compute_pentagon_scores_gk(player_data, comparison_df, all_cols):
    """Calcula los 5 puntajes del pentágono para porteros.
    Ejes: REF (reflejos), EFE (efectividad), DIS (distribución),
          DISP (distribución de peligro), ALCP (alcance de pase)."""
    axis_scores = {}
    for axis, cols in _GK_PENTAGON_COLS.items():
        pcts = []
        for c in cols:
            if c not in comparison_df.columns:
                continue
            val = player_data.get(c, None)
            if val is None or pd.isnull(val):
                continue
            pct = _compute_percentile(float(val), comparison_df[c])
            if c in _GK_LOWER_IS_BETTER_PENT:
                pct = max(0, 99 - pct)
            pcts.append(pct)
        axis_scores[axis] = int(round(float(np.mean(pcts)))) if pcts else 0
    return axis_scores


def _compute_avg_pentagon_scores_gk(comparison_df, all_cols):
    """Puntaje promedio del pentágono GK para el pool de comparación."""
    axis_scores = {}
    for axis, cols in _GK_PENTAGON_COLS.items():
        axis_pcts = []
        for c in cols:
            if c not in comparison_df.columns:
                continue
            col_vals = pd.to_numeric(comparison_df[c], errors='coerce').dropna()
            if len(col_vals) == 0:
                continue
            pcts = [0 if v == 0.0 else int(np.sum(col_vals <= v) / len(col_vals) * 99)
                    for v in col_vals]
            if c in _GK_LOWER_IS_BETTER_PENT:
                pcts = [max(0, 99 - p) for p in pcts]
            axis_pcts.append(float(np.mean(pcts)))
        axis_scores[axis] = int(round(float(np.mean(axis_pcts)))) if axis_pcts else 0
    return axis_scores


def _create_pentagon_chart(scores, player_name, team, subtitle, avg_scores=None,
                           pos_label='', scores2=None, player2_name='',
                           custom_labels=None):
    """Dibuja el gráfico pentágono estilo Sofascore con matplotlib.
    Si scores2 se provee, dibuja dos polígonos (verde P1, azul P2) y badges apilados.
    custom_labels: lista de 5 claves si se usan ejes distintos (ej. GK)."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    labels     = custom_labels if custom_labels else ['ATQ', 'POS', 'PAS', 'DEF', 'CRE']
    angles     = [np.radians(90 - i * 72) for i in range(5)]
    score_vals = [scores.get(l, 0) for l in labels]
    norm_vals  = [s / 99.0 for s in score_vals]

    bg_x = [np.cos(a) for a in angles]
    bg_y = [np.sin(a) for a in angles]
    pl_x = [v * np.cos(a) for v, a in zip(norm_vals, angles)]
    pl_y = [v * np.sin(a) for v, a in zip(norm_vals, angles)]

    compare_mode = bool(scores2 and player2_name)

    fig, ax = plt.subplots(figsize=(6.5, 7.4), facecolor='#0f1117')
    ax.set_facecolor('#0f1117')
    ax.set_aspect('equal')
    ax.axis('off')

    # Fondo del pentágono
    bg_poly = plt.Polygon(list(zip(bg_x, bg_y)), closed=True,
                          facecolor='#1a1f2e', edgecolor='#2d3748', linewidth=1.5)
    ax.add_patch(bg_poly)

    # Líneas de grilla (25 %, 50 %, 75 %)
    for pct in [0.25, 0.50, 0.75]:
        gx = [pct * np.cos(a) for a in angles] + [pct * np.cos(angles[0])]
        gy = [pct * np.sin(a) for a in angles] + [pct * np.sin(angles[0])]
        ax.plot(gx, gy, color='#2d3748', linewidth=0.6, alpha=0.6)

    # Ejes radiales
    for a in angles:
        ax.plot([0, np.cos(a)], [0, np.sin(a)], color='#2d3748', linewidth=0.6, alpha=0.6)

    # Polígono promedio de la posición (punteado gris)
    if avg_scores:
        avg_vals = [avg_scores.get(l, 0) / 99.0 for l in labels]
        avg_x = [v * np.cos(a) for v, a in zip(avg_vals, angles)]
        avg_y = [v * np.sin(a) for v, a in zip(avg_vals, angles)]
        avg_poly = plt.Polygon(list(zip(avg_x, avg_y)), closed=True,
                               fill=False, edgecolor='#94a3b8', linewidth=1.6,
                               linestyle='--', alpha=0.8, zorder=3)
        ax.add_patch(avg_poly)
        for lbl, ang, sc in zip(labels, angles, [avg_scores.get(l, 0) for l in labels]):
            ax.text(0.88 * np.cos(ang), 0.88 * np.sin(ang), str(sc),
                    ha='center', va='center', fontsize=7.5,
                    color='#94a3b8', alpha=0.85, zorder=4)

    # Polígono jugador 2 (azul, debajo del jugador 1)
    if compare_mode:
        score2_vals = [scores2.get(l, 0) for l in labels]
        norm2_vals  = [s / 99.0 for s in score2_vals]
        pl2_x = [v * np.cos(a) for v, a in zip(norm2_vals, angles)]
        pl2_y = [v * np.sin(a) for v, a in zip(norm2_vals, angles)]
        pl2_poly = plt.Polygon(list(zip(pl2_x, pl2_y)), closed=True,
                               facecolor='#f9731625', edgecolor='#f97316', linewidth=2.5,
                               zorder=4)
        ax.add_patch(pl2_poly)

    # Polígono jugador 1 (sky blue, encima)
    pl_poly = plt.Polygon(list(zip(pl_x, pl_y)), closed=True,
                          facecolor='#0ea5e925', edgecolor='#0ea5e9', linewidth=2.5,
                          zorder=5)
    ax.add_patch(pl_poly)

    # Punto central
    ax.plot(0, 0, 'o', color='#0ea5e9', markersize=5, zorder=7)
    if compare_mode:
        ax.plot(0, 0, 'o', color='#f97316', markersize=3, zorder=8)

    # Badges en vértices
    offset = 1.36
    for label, angle, score in zip(labels, angles, score_vals):
        bx = offset * np.cos(angle)
        by = offset * np.sin(angle)
        avg_val = avg_scores.get(label, 50) if avg_scores else 50

        if compare_mode:
            sc2 = scores2.get(label, 0)
            # Badge P1 siempre sky blue (color de referencia)
            ax.text(bx, by + 0.20, str(score), ha='center', va='center',
                    fontsize=13, fontweight='bold', color='#fff',
                    bbox=dict(boxstyle='round,pad=0.26', facecolor='#0369a1', edgecolor='none'),
                    zorder=9)
            # Badge P2 siempre naranja (color de referencia)
            ax.text(bx, by - 0.02, str(sc2), ha='center', va='center',
                    fontsize=13, fontweight='bold', color='#fff',
                    bbox=dict(boxstyle='round,pad=0.26', facecolor='#c2410c', edgecolor='none'),
                    zorder=9)
            ax.text(bx, by - 0.26, label, ha='center', va='center',
                    fontsize=10, fontweight='bold', color='#9ca3af', zorder=9)
        else:
            # Badge único (modo individual)
            if score >= 70 and score > avg_val:
                badge_col, txt_col = '#ca8a04', '#fff'
            elif score >= avg_val:
                badge_col, txt_col = '#0369a1', '#fff'
            else:
                badge_col, txt_col = '#374151', '#d1d5db'

            ax.text(bx, by + 0.09, str(score), ha='center', va='center',
                    fontsize=17, fontweight='bold', color=txt_col,
                    bbox=dict(boxstyle='round,pad=0.32', facecolor=badge_col, edgecolor='none'),
                    zorder=7)
            ax.text(bx, by - 0.15, label, ha='center', va='center',
                    fontsize=11, fontweight='bold', color='#9ca3af', zorder=7)

    ax.set_xlim(-1.78, 1.78)
    ax.set_ylim(-1.78, 1.92)

    # Título
    if compare_mode:
        title_text = f'{player_name}  ⚔  {player2_name}'
        title_fs   = 12
    else:
        title_text = player_name
        title_fs   = 15
    ax.text(0, 1.88, title_text, ha='center', va='top',
            fontsize=title_fs, fontweight='bold', color='white')
    ax.text(0, 1.70, f'{team}  ·  {subtitle}', ha='center', va='top',
            fontsize=9.5, color='#6b7280')

    # Leyenda — colores alineados con los polígonos del gráfico
    # P1: sky blue (#0ea5e9) · P2: naranja (#f97316)
    if compare_mode:
        legend_items = [
            mpatches.Patch(color='#0ea5e9', label=f'■ {player_name[:18]}'),
            mpatches.Patch(color='#f97316', label=f'■ {player2_name[:18]}'),
            mpatches.Patch(facecolor='none', edgecolor='#94a3b8',
                           linestyle='--', label=f'Prom. {pos_label}'),
            mpatches.Patch(color='#ca8a04', label='Dest. P1 (≥70 y sobre prom.)'),
        ]
    else:
        legend_items = [
            mpatches.Patch(color='#0ea5e9', label='Jugador'),
            mpatches.Patch(facecolor='none', edgecolor='#94a3b8',
                           linestyle='--', label=f'Promedio {pos_label}'),
            mpatches.Patch(color='#ca8a04', label='Destacado (≥70 y sobre prom.)'),
            mpatches.Patch(color='#0369a1', label='Sobre el promedio'),
            mpatches.Patch(color='#374151', label='Bajo el promedio'),
        ]
    ax.legend(handles=legend_items, loc='lower center', ncol=2,
              facecolor='#0f1117', edgecolor='#2d3748',
              labelcolor='#9ca3af', fontsize=7.8,
              bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout(pad=0.3)

    fig.text(0.5, 0.1, '𝕏: @marca_zonal  ·  Instagram: @marca.zonal',
             size=7.5, color='#6b7280', ha='center', fontstyle='italic')

    return fig


with tab_table:
    # Determine team column
    team_col_tab1 = 'Team within selected timeframe'
    if team_col_tab1 not in df.columns:
        team_col_tab1 = 'Team'

    # 3 cascading dropdowns
    col_pos, col_club, col_player = st.columns(3)

    position_groups = sorted(df['Position Group'].dropna().unique())
    with col_pos:
        selected_pos = st.selectbox("Posición", position_groups, key="tab1_pos")

    pos_df = df[df['Position Group'] == selected_pos]
    clubs_in_pos = sorted(pos_df[team_col_tab1].dropna().unique())
    with col_club:
        selected_club = st.selectbox("Club", clubs_in_pos, key="tab1_club")

    club_pos_df = pos_df[pos_df[team_col_tab1] == selected_club]
    players_list = sorted(club_pos_df['Player'].dropna().unique())
    with col_player:
        selected_player_tab1 = st.selectbox("Jugador", players_list, key="tab1_player")

    # Min-minutes slider — rango calculado sobre la posición seleccionada
    _mp = pos_df['Minutes played'] if 'Minutes played' in pos_df.columns else None
    t1_min_v = int(_mp.min()) if _mp is not None and len(pos_df) > 0 else 0
    t1_max_v = int(_mp.max()) if _mp is not None and len(pos_df) > 0 else 100
    if t1_min_v >= t1_max_v:
        t1_max_v = t1_min_v + 1
    tab1_min_minutes = st.slider(
        "Minutos mínimos (para percentiles)", t1_min_v, t1_max_v,
        value=min(200, t1_max_v), key=f"tab1_min_minutes_{selected_pos}"
    )

    # Display selected player data
    player_rows = club_pos_df[club_pos_df['Player'] == selected_player_tab1]
    if not player_rows.empty:
        player_data = player_rows.iloc[0]

        # Player header card (campo táctico + stats)
        components.html(
            _player_header_html(
                player_name=selected_player_tab1,
                position_code=str(player_data.get('Position', '')),
                pos_group=selected_pos,
                team=str(player_data.get(team_col_tab1, '')),
                age=player_data.get('Age', None),
                matches=player_data.get('Matches played', None),
                minutes=player_data.get('Minutes played', None),
            ),
            height=210,
        )

        # Bloqueo por minutos — el jugador seleccionado también debe cumplir el mínimo
        _player_mins = player_data.get('Minutes played', None)
        _player_mins_val = float(_player_mins) if _player_mins is not None and pd.notnull(_player_mins) else 0
        _below_threshold = _player_mins_val < tab1_min_minutes
        if _below_threshold:
            st.warning(
                f"⚠️ **{selected_player_tab1}** tiene **{int(_player_mins_val)} minutos** jugados, "
                f"por debajo del mínimo de **{tab1_min_minutes} min** del filtro. "
                f"Bajá el slider para ver sus percentiles."
            )

        if not _below_threshold:
            # Comparison pool info
            comparison_df = df[
                (df['Position Group'] == selected_pos) &
                (df['Minutes played'] >= tab1_min_minutes)
            ].copy()
            n_comp = len(comparison_df)
            st.caption(
                f"Percentiles vs. **{n_comp} {selected_pos.lower()}s** "
                f"con \u2265 {tab1_min_minutes} min · Apertura 2026"
            )
            st.markdown("---")

            # Métricas curadas — rama portero vs. outfield
            is_gk = (selected_pos == 'Portero')
            if is_gk:
                show_cols   = _get_display_cols_gk(df)
                cat_fn      = categorize_metric_gk
                cat_order   = GK_CATEGORY_ORDER
                cat_colors  = GK_CATEGORY_COLORS
            else:
                show_cols   = _get_display_cols(df)
                cat_fn      = categorize_metric
                cat_order   = CATEGORY_ORDER
                cat_colors  = CATEGORY_COLORS

            # Group and compute percentiles
            categorized = defaultdict(list)
            for c in show_cols:
                val = player_data.get(c, None)
                if pd.isnull(val):
                    continue
                player_val = float(val)
                pct = _compute_percentile(player_val, comparison_df[c]) if c in comparison_df.columns else 0
                if c in _GK_LOWER_IS_BETTER:
                    pct = max(0, 99 - pct)
                formatted = f"{player_val:.2f}"
                cat = cat_fn(c)
                categorized[cat].append({
                    'metric': translate(c),
                    'value':  formatted,
                    'pct':    pct,
                })

            # Render bars — all categories in one component call
            if categorized:
                _render_all_bars(categorized, cat_order, cat_colors)
            else:
                st.info("No hay métricas disponibles para mostrar.")
    elif players_list:
        st.info("Selecciona un jugador para ver sus datos.")

# ---- Tab 2: XY Chart -----------------------------------------------------
with tab_xy:
    st.subheader("Gráfico XY comparativo")

    # Position & player selectors (replacing removed sidebar)
    xy_position_groups = sorted(df['Position Group'].dropna().unique())
    xy_sel1, xy_sel2 = st.columns(2)
    with xy_sel1:
        xy_pos_group = st.selectbox("Grupo de posición", xy_position_groups, key="xy_pos_group")
    xy_group_df = df[df['Position Group'] == xy_pos_group].copy()
    xy_players = sorted(xy_group_df['Player'].dropna().unique())
    with xy_sel2:
        xy_selected_player = st.selectbox("Jugador destacado", xy_players, key="xy_player")

    # Only per-90 metrics — métricas GK exclusivas solo si se selecciona Portero
    xy_is_gk = (xy_pos_group == 'Portero')
    per90_columns = sorted([
        c for c in metric_columns
        if c.endswith(' per 90')
        and (xy_is_gk or c not in _GK_ONLY_METRICS)
    ])
    if not per90_columns:
        st.warning("No se encontraron métricas 'por 90' en los datos.")
    else:
        # Minutes slider
        min_min = int(xy_group_df['Minutes played'].min()) if 'Minutes played' in xy_group_df.columns else 0
        max_min = int(xy_group_df['Minutes played'].max()) if 'Minutes played' in xy_group_df.columns else 100
        min_minutes = st.slider(
            "Minutos mínimos jugados", min_min, max_min,
            value=min(200, max_min), key="xy_min_minutes"
        )

        col1, col2 = st.columns(2)
        with col1:
            x_metric = st.selectbox("Métrica eje X", per90_columns, key="xy_x",
                                     format_func=translate)
        with col2:
            y_metric = st.selectbox("Métrica eje Y", per90_columns,
                                     index=min(1, len(per90_columns) - 1),
                                     key="xy_y", format_func=translate)

        # Filter by minutes played
        xy_df = xy_group_df[xy_group_df['Minutes played'] >= min_minutes].copy()
        xy_df = xy_df[['Player', x_metric, y_metric]].dropna()

        if len(xy_df) < 2:
            st.warning("No hay suficientes datos para generar el gráfico. Prueba reducir los minutos mínimos.")
        else:
            fig_xy = create_xy_chart(xy_df, x_metric, y_metric, xy_selected_player,
                                     x_label=translate(x_metric),
                                     y_label=translate(y_metric),
                                     logo_path=LOGO_BLANCO)
            st.pyplot(fig_xy)

            # Download button
            buf = io.BytesIO()
            fig_xy.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                           facecolor=fig_xy.get_facecolor())
            st.download_button("⬇️ Descargar grafica", buf.getvalue(),
                               file_name="grafico_xy_marcazonal.png", mime="image/png")
            st.caption("𝕏: @marca_zonal  ·  Instagram: @marca.zonal")

# ---- Tab 3: Resumen Pentágono estilo Sofascore ----------------------------
with tab_bar:
    st.subheader("Resumen de atributos")
    st.caption("Puntaje compuesto (0–99) por macro-categoría, calculado como promedio de percentiles")

    # Inicializar session state para el comparador
    if 'pent_show_compare' not in st.session_state:
        st.session_state['pent_show_compare'] = False

    # Selectores: Posición → Club → Jugador
    pent_team_col = 'Team within selected timeframe'
    if pent_team_col not in df.columns:
        pent_team_col = 'Team'

    pent_col1, pent_col2, pent_col3 = st.columns(3)
    pent_pos_groups = sorted([p for p in df['Position Group'].dropna().unique()
                               if p != 'Portero'])
    pent_pos_groups_all = ['Portero'] + pent_pos_groups   # GK al final del selectbox
    pent_pos_groups_all = sorted(df['Position Group'].dropna().unique())
    with pent_col1:
        pent_pos = st.selectbox("Posición", pent_pos_groups_all, key="pent_pos")
    pent_pos_df = df[df['Position Group'] == pent_pos]
    pent_clubs  = sorted(pent_pos_df[pent_team_col].dropna().unique())
    with pent_col2:
        pent_club = st.selectbox("Club", pent_clubs, key="pent_club")
    pent_club_df = pent_pos_df[pent_pos_df[pent_team_col] == pent_club]
    pent_players = sorted(pent_club_df['Player'].dropna().unique())
    with pent_col3:
        pent_player = st.selectbox("Jugador", pent_players, key="pent_player")

    # Slider de minutos mínimos para el pool de comparación
    pent_min_v = int(df['Minutes played'].min()) if 'Minutes played' in df.columns else 0
    pent_max_v = int(df['Minutes played'].max()) if 'Minutes played' in df.columns else 100
    pent_min_minutes = st.slider(
        "Minutos mínimos (pool de comparación)", pent_min_v, pent_max_v,
        value=min(200, pent_max_v), key="pent_min_minutes"
    )

    # Botón "Comparar" (toggle)
    compare_label = "❌ Cancelar comparación" if st.session_state['pent_show_compare'] else "⚔️ Comparar jugadores"
    if st.button(compare_label, key="btn_comparar"):
        st.session_state['pent_show_compare'] = not st.session_state['pent_show_compare']
        st.rerun()

    # Selectores del segundo jugador (misma posición)
    pent_player2 = None
    pent_club2   = None
    if st.session_state['pent_show_compare']:
        st.markdown("---")
        st.markdown("**Segundo jugador** *(misma posición: {})*".format(pent_pos))
        cmp_col1, cmp_col2 = st.columns(2)
        with cmp_col1:
            pent_club2 = st.selectbox("Club (jugador 2)", pent_clubs, key="pent_club2")
        cmp_club_df = pent_pos_df[pent_pos_df[pent_team_col] == pent_club2]
        cmp_players = sorted(cmp_club_df['Player'].dropna().unique())
        # Excluir al jugador 1 de la lista
        cmp_players_filt = [p for p in cmp_players if p != pent_player] or cmp_players
        with cmp_col2:
            pent_player2 = st.selectbox("Jugador 2", cmp_players_filt, key="pent_player2")
        st.markdown("---")

    pent_player_rows = pent_club_df[pent_club_df['Player'] == pent_player]
    if pent_player_rows.empty:
        st.warning("Jugador no encontrado.")
    else:
        pent_player_data = pent_player_rows.iloc[0]
        pent_comparison_df = df[
            (df['Position Group'] == pent_pos) &
            (df['Minutes played'] >= pent_min_minutes)
        ].copy()
        n_pent = len(pent_comparison_df)

        if pent_comparison_df[pent_comparison_df['Player'] == pent_player].empty:
            st.warning("El jugador no alcanza el mínimo de minutos. Reducí el slider.")
        else:
            # Rama portero vs. outfield
            is_pent_gk = (pent_pos == 'Portero')
            if is_pent_gk:
                all_pent_cols  = _get_display_cols_gk(df)
                scores         = _compute_pentagon_scores_gk(
                    pent_player_data, pent_comparison_df, all_pent_cols)
                avg_scores     = _compute_avg_pentagon_scores_gk(pent_comparison_df, all_pent_cols)
                pent_axes      = ['REF', 'EFE', 'DIS', 'DISP', 'ALCP']
                pent_group_desc = {
                    'REF':  'Reflejos (remates recibidos, efectividad de atajadas)',
                    'EFE':  'Efectividad (goles concedidos, xG en contra, goles evitados)',
                    'DIS':  'Distribución (precisión de pases generales)',
                    'DISP': 'Distribución de peligro (pases al último tercio, área y progresivos)',
                    'ALCP': 'Alcance de pase (longitud promedio de pases)',
                }
            else:
                all_pent_cols  = _get_display_cols(df)
                scores         = _compute_pentagon_scores(
                    pent_player_data, pent_comparison_df, all_pent_cols)
                avg_scores     = _compute_avg_pentagon_scores(pent_comparison_df, all_pent_cols)
                pent_axes      = ['ATQ', 'POS', 'PAS', 'CRE', 'DEF']
                pent_group_desc = {
                    'ATQ': 'Goles y Remates',
                    'POS': 'Posesión (Dribbling, Recepción, Acciones ofensivas)',
                    'PAS': 'Pases y Centros',
                    'CRE': 'Creatividad',
                    'DEF': 'Defensa y Duelos (con penalización por Disciplina)',
                }

            # Calcular scores del jugador 2 si el comparador está activo
            scores2 = None
            if st.session_state['pent_show_compare'] and pent_player2:
                p2_rows = pent_pos_df[pent_pos_df['Player'] == pent_player2]
                if not p2_rows.empty:
                    p2_data = p2_rows.iloc[0]
                    if is_pent_gk:
                        scores2 = _compute_pentagon_scores_gk(p2_data, pent_comparison_df, all_pent_cols)
                    else:
                        scores2 = _compute_pentagon_scores(p2_data, pent_comparison_df, all_pent_cols)

            team_display = str(pent_player_data.get(pent_team_col, ''))
            subtitle_pent = f"vs. {n_pent} {pent_pos.lower()}s · +{pent_min_minutes} min · Apertura 2026"

            # Centrar el gráfico
            _, col_center, _ = st.columns([1, 2, 1])
            with col_center:
                fig_pent = _create_pentagon_chart(
                    scores, pent_player, team_display, subtitle_pent,
                    avg_scores=avg_scores, pos_label=pent_pos,
                    scores2=scores2, player2_name=pent_player2 or '',
                    custom_labels=pent_axes if is_pent_gk else None,
                )
                st.pyplot(fig_pent)

                buf_pent = io.BytesIO()
                fig_pent.savefig(buf_pent, format='png', dpi=200, bbox_inches='tight',
                                 facecolor=fig_pent.get_facecolor())
                dl_fname = (
                    f"pentagono_{pent_player.replace(' ', '_')}_vs_{pent_player2.replace(' ', '_')}.png"
                    if scores2 and pent_player2
                    else f"pentagono_{pent_player.replace(' ', '_')}.png"
                )
                st.download_button(
                    "⬇️ Descargar gráfico", buf_pent.getvalue(),
                    file_name=dl_fname,
                    mime="image/png", key="dl_pent"
                )
                st.caption("𝕏: @marca_zonal  ·  Instagram: @marca.zonal")

            # Tabla resumen de puntajes debajo del gráfico
            st.markdown("#### Detalle de puntajes")
            summary_rows = []
            for key in pent_axes:
                diff = scores[key] - avg_scores[key]
                row = {
                    'Categoría': key,
                    'Descripción': pent_group_desc[key],
                    pent_player[:20]: scores[key],
                    f'Prom. {pent_pos}': avg_scores[key],
                    'Dif. P1': f"+{diff}" if diff >= 0 else str(diff),
                }
                if scores2 and pent_player2:
                    diff2 = scores2[key] - avg_scores[key]
                    row[pent_player2[:20]] = scores2[key]
                    row['Dif. P2'] = f"+{diff2}" if diff2 >= 0 else str(diff2)
                summary_rows.append(row)
            st.dataframe(
                pd.DataFrame(summary_rows),
                use_container_width=True,
                hide_index=True,
            )

# ---- Tab 4: Pizza/Radar Chart ---------------------------------------------
with tab_pizza:
    st.subheader("Gráfico Radial por percentiles")

    # Club → Player selection
    pizza_team_col = 'Team within selected timeframe'
    if pizza_team_col not in df.columns:
        pizza_team_col = 'Team'
    pizza_all_clubs = sorted(df[pizza_team_col].dropna().unique())

    pizza_col1, pizza_col2, pizza_col3 = st.columns(3)
    with pizza_col1:
        pizza_club = st.selectbox("Club", pizza_all_clubs, key="pizza_club")

    # Filter positions available in the selected club
    pizza_club_df = df[df[pizza_team_col] == pizza_club]
    pizza_positions = sorted(pizza_club_df['Position Group'].dropna().unique())
    with pizza_col2:
        pizza_position = st.selectbox("Posición", pizza_positions, key="pizza_position")

    # Filter players by club + position
    pizza_club_pos_df = pizza_club_df[pizza_club_df['Position Group'] == pizza_position]
    pizza_club_players = sorted(pizza_club_pos_df['Player'].dropna().unique())
    with pizza_col3:
        pizza_player = st.selectbox("Jugador", pizza_club_players, key="pizza_player")

    # Minutes slider
    pizza_min_min = int(df['Minutes played'].min()) if 'Minutes played' in df.columns else 0
    pizza_max_min = int(df['Minutes played'].max()) if 'Minutes played' in df.columns else 100
    pizza_min_minutes = st.slider(
        "Minutos mínimos jugados", pizza_min_min, pizza_max_min,
        value=min(200, pizza_max_min), key="pizza_min_minutes"
    )

    # Find the player's position group
    pizza_player_rows = df[df['Player'] == pizza_player]
    if pizza_player_rows.empty:
        st.warning("Jugador no encontrado.")
    else:
        pizza_player_data = pizza_player_rows.iloc[0]
        pizza_pos_group = pizza_player_data.get('Position Group', None)

        if pd.isna(pizza_pos_group):
            st.warning("El jugador no tiene grupo de posición asignado.")
        else:
            # Filter comparison group: same position group + min minutes
            pizza_group_df = df[
                (df['Position Group'] == pizza_pos_group)
                & (df['Minutes played'] >= pizza_min_minutes)
            ].copy()

            pizza_player_in_group = pizza_group_df[pizza_group_df['Player'] == pizza_player]
            if pizza_player_in_group.empty:
                st.warning("El jugador no cumple el filtro de minutos mínimos. Reducí el slider.")
            else:
                pizza_player_data = pizza_player_in_group.iloc[0]
                n_pizza_players = len(pizza_group_df)

                # Build params, values, min_range, max_range from PIZZA_METRICS
                params = []
                values = []
                min_range = []
                max_range = []

                for cat_name, metric_list in PIZZA_METRICS.items():
                    for m in metric_list:
                        if m not in pizza_group_df.columns:
                            continue
                        col = pd.to_numeric(pizza_group_df[m], errors='coerce')
                        val = pd.to_numeric(pizza_player_data[m], errors='coerce')
                        mn = float(col.min()) if pd.notnull(col.min()) else 0
                        mx = float(col.max()) if pd.notnull(col.max()) else 1
                        if mn == mx:
                            mx = mn + 1
                        v = float(val) if pd.notnull(val) else 0
                        params.append(translate(m))
                        values.append(round(v, 2))
                        min_range.append(round(mn, 2))
                        max_range.append(round(mx, 2))

                if len(params) < 3:
                    st.warning("No hay suficientes métricas para generar el gráfico radial.")
                else:
                    team_display = str(pizza_player_data.get(pizza_team_col, ''))
                    subtitle = f"Entre {n_pizza_players} {pizza_pos_group.lower()}s +{pizza_min_minutes} min | Apertura 2026"

                    fig_pizza = create_pizza_chart(
                        player_name=pizza_player,
                        player_team=team_display,
                        subtitle=subtitle,
                        params=params,
                        values=values,
                        min_range=min_range,
                        max_range=max_range,
                        center_image=LOGO_BLANCO,
                    )
                    st.pyplot(fig_pizza)

                    buf3 = io.BytesIO()
                    fig_pizza.savefig(buf3, format='png', dpi=200, bbox_inches='tight',
                                     facecolor=fig_pizza.get_facecolor())
                    st.download_button("⬇️ Descargar gráfica", buf3.getvalue(),
                                       file_name="radial_marcazonal.png", mime="image/png",
                                       key="dl_pizza")
                    st.caption("𝕏: @marca_zonal  ·  Instagram: @marca.zonal")

# ---- Tab 5: Jugadores Similares -------------------------------------------
def _get_similarity_cols(df):
    """Columnas para el PCA de similitud: todas las per-90 y % numéricas disponibles."""
    return [
        c for c in df.columns
        if (c.endswith(' per 90') or c.endswith(', %'))
        and c not in NON_METRIC_COLS
        and pd.api.types.is_numeric_dtype(df[c])
    ]


def _compute_similarity_scores(pool_df, player_name):
    """
    Calcula puntajes de similitud (0–100%) vs todos los jugadores del pool.

    Flujo:
      1. Seleccionar métricas per-90 y %
      2. Imputar NaN con 0
      3. Eliminar columnas de varianza cero
      4. StandardScaler → PCA (componentes que expliquen ≥85% de varianza)
      5. Distancia euclídea en espacio PCA
      6. Similitud % = (1 - dist / max_dist) * 100
    """
    sim_cols = _get_similarity_cols(pool_df)
    if len(sim_cols) < 3:
        return None, 0, 0.0

    X_raw = pool_df[sim_cols].fillna(0).copy()

    # Eliminar columnas de varianza cero
    var_mask = X_raw.var() > 0
    X_raw = X_raw.loc[:, var_mask]
    n_features = X_raw.shape[1]
    n_samples = X_raw.shape[0]

    if n_features < 2 or n_samples < 3:
        return None, 0, 0.0

    # Estandarizar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # PCA — componentes para ≥85% varianza, mínimo 3, máximo 25
    max_comp = min(n_features, n_samples - 1, 25)
    pca_full = PCA(n_components=max_comp, random_state=42)
    pca_full.fit(X_scaled)
    cumvar = np.cumsum(pca_full.explained_variance_ratio_)
    n_comp = int(np.argmax(cumvar >= 0.85)) + 1
    n_comp = max(3, min(n_comp, max_comp))

    pca = PCA(n_components=n_comp, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    var_explained = float(np.sum(pca.explained_variance_ratio_) * 100)

    # Índice del jugador seleccionado
    players_reset = pool_df['Player'].reset_index(drop=True)
    player_mask = players_reset == player_name
    if not player_mask.any():
        return None, n_comp, var_explained

    player_idx = int(player_mask.idxmax())
    player_vec = X_pca[player_idx]

    # Distancias euclídeas
    distances = np.sqrt(np.sum((X_pca - player_vec) ** 2, axis=1))
    max_dist = distances.max()
    similarities = (1 - distances / max_dist) * 100.0 if max_dist > 0 else np.ones(len(distances)) * 100.0

    # Armar DataFrame de resultados
    results = pool_df[['Player']].copy().reset_index(drop=True)
    results['Similitud'] = np.round(similarities, 1)
    results = results[results['Player'] != player_name]
    results = results.sort_values('Similitud', ascending=False).reset_index(drop=True)
    results.index += 1

    return results, n_comp, var_explained


def _create_similarity_card(player_name, player_team, player_age, player_pos,
                            player_mins, results, pool_df, team_col,
                            n_comp, var_explained, top_n=10, logo_path=None):
    """Genera una figura matplotlib descargable con la tarjeta de jugadores similares."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.image as mpimg
    from matplotlib.patches import FancyBboxPatch

    top = results.head(top_n).copy()
    n_rows = len(top)
    fig_h = 2.8 + n_rows * 0.52
    fig, ax = plt.subplots(figsize=(10, fig_h), facecolor='#0e1117')
    ax.set_facecolor('#0e1117')
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, fig_h)

    y = fig_h

    # ── Header del jugador ──────────────────────────────────────────────────
    header_h = 1.0
    header_box = FancyBboxPatch((0.15, y - header_h - 0.15), 9.7, header_h,
                                boxstyle="round,pad=0.08",
                                facecolor='#1a1f2e', edgecolor='#2d3748', linewidth=1)
    ax.add_patch(header_box)
    ax.text(0.45, y - 0.38, player_name, fontsize=17, fontweight='bold',
            color='#f1f5f9', va='top')
    info_str = f"{player_team}  ·  {player_pos}  ·  {player_age} años  ·  {player_mins:,} mins"
    ax.text(0.45, y - 0.72, info_str, fontsize=9, color='#9ca3af', va='top')
    ax.text(9.65, y - 0.38,
            f"PCA: {n_comp} comp.  ·  {var_explained:.1f}% var.",
            fontsize=8, color='#6b7280', va='top', ha='right')
    y -= (header_h + 0.35)

    # ── Encabezado de columnas ──────────────────────────────────────────────
    ax.axhline(y, color='#2d3748', linewidth=0.8)
    for txt, xpos, align in [
        ('#',     0.35, 'center'),
        ('Jugador', 0.65, 'left'),
        ('Equipo',  3.80, 'left'),
        ('Pos.',    6.00, 'left'),
        ('Edad',    7.00, 'center'),
        ('Mins',    7.75, 'right'),
        ('Similitud', 9.65, 'right'),
    ]:
        ax.text(xpos, y - 0.08, txt.upper(), fontsize=7.5, color='#6b7280',
                fontweight='bold', va='top', ha=align)
    y -= 0.42
    ax.axhline(y + 0.22, color='#2d3748', linewidth=0.5)

    # ── Filas ───────────────────────────────────────────────────────────────
    for rank, row in top.iterrows():
        pname = row['Player']
        sim   = row['Similitud']
        info  = pool_df[pool_df['Player'] == pname]
        team  = str(info[team_col].values[0]) if not info.empty else '—'
        pos   = str(info['Position Group'].values[0]) if not info.empty else '—'
        mins  = int(info['Minutes played'].values[0]) if not info.empty else 0
        age_r = info['Age'].values[0] if (not info.empty and 'Age' in info.columns) else None
        age   = int(age_r) if age_r is not None and pd.notnull(age_r) else '—'

        # Color barra
        if sim >= 85:   bar_col = '#22c55e'
        elif sim >= 70: bar_col = '#84cc16'
        elif sim >= 55: bar_col = '#eab308'
        else:           bar_col = '#f97316'

        row_y = y - 0.08
        # Barra de fondo
        bar_bg = FancyBboxPatch((8.05, row_y - 0.26), 1.50, 0.34,
                                boxstyle="round,pad=0.02",
                                facecolor='#1f2937', edgecolor='none')
        ax.add_patch(bar_bg)
        # Barra relleno
        bar_w = 1.50 * (sim / 100.0)
        bar_fill = FancyBboxPatch((8.05, row_y - 0.26), bar_w, 0.34,
                                  boxstyle="round,pad=0.02",
                                  facecolor=bar_col, edgecolor='none', alpha=0.85)
        ax.add_patch(bar_fill)

        ax.text(0.35, row_y, str(rank),    fontsize=9,  color='#4b5563', va='center', ha='center', fontweight='bold')
        ax.text(0.65, row_y, pname[:26],   fontsize=9.5, color='#f1f5f9', va='center', ha='left', fontweight='bold')
        ax.text(3.80, row_y, team[:22],    fontsize=8.5, color='#9ca3af', va='center', ha='left')
        ax.text(6.00, row_y, pos[:14],     fontsize=7.5, color='#6b7280', va='center', ha='left')
        ax.text(7.00, row_y, str(age),     fontsize=8.5, color='#4ade80', va='center', ha='center', fontweight='bold')
        ax.text(7.75, row_y, f'{mins:,}',  fontsize=7.5, color='#6b7280', va='center', ha='right')
        ax.text(9.65, row_y, f'{sim:.1f}%', fontsize=9.5, color='#fff',   va='center', ha='right', fontweight='bold')

        y -= 0.52
        ax.axhline(y + 0.28, color='#1a1f2e', linewidth=0.5)

    # ── Footer / branding ───────────────────────────────────────────────────
    ax.axhline(0.32, color='#2d3748', linewidth=0.8)
    ax.text(5.0, 0.22, 'MARCA ZONAL · Jugadores Similares · PCA + Distancia Euclídea',
            fontsize=7.5, color='#374151', va='center', ha='center', fontstyle='italic')
    ax.text(5.0, 0.07, '𝕏: @marca_zonal  ·  Instagram: @marca.zonal',
            fontsize=7.5, color='#4b5563', va='center', ha='center', fontstyle='italic')

    plt.tight_layout(pad=0.4)
    return fig


def _render_similarity_table(results, pool_df, team_col, top_n):
    """Renderiza la tabla de similitud como HTML con barras de porcentaje."""
    rows_html = ''
    for rank, row in results.head(top_n).iterrows():
        pname = row['Player']
        sim   = row['Similitud']

        player_info = pool_df[pool_df['Player'] == pname]
        team  = str(player_info[team_col].values[0]) if not player_info.empty else '—'
        pos   = str(player_info['Position Group'].values[0]) if not player_info.empty else '—'
        mins  = int(player_info['Minutes played'].values[0]) if not player_info.empty else 0
        age_raw = player_info['Age'].values[0] if (not player_info.empty and 'Age' in player_info.columns) else None
        age   = int(age_raw) if age_raw is not None and pd.notnull(age_raw) else '—'

        # Color de barra según similitud
        if sim >= 85:
            bar_color = '#22c55e'
        elif sim >= 70:
            bar_color = '#84cc16'
        elif sim >= 55:
            bar_color = '#eab308'
        else:
            bar_color = '#f97316'

        bar_w = max(int(sim), 2)
        rows_html += f"""
        <tr>
          <td class="rank">{rank}</td>
          <td class="pname">{pname}</td>
          <td class="team">{team}</td>
          <td class="pos">{pos}</td>
          <td class="age">{age}</td>
          <td class="mins">{mins:,}</td>
          <td class="bar-cell">
            <div class="bar-bg">
              <div class="bar-fill" style="width:{bar_w}%; background:{bar_color};"></div>
              <span class="bar-label">{sim:.1f}%</span>
            </div>
          </td>
        </tr>"""

    n_rows = min(top_n, len(results))
    height = n_rows * 44 + 90

    html = f"""<!DOCTYPE html><html><head><style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Cousine', monospace; background: #0e1117; color: #b0b8c8; padding: 6px 2px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
        font-size: 10px; font-weight: 700; color: #6b7280;
        text-transform: uppercase; letter-spacing: 1px;
        padding: 8px 10px; border-bottom: 1px solid #2d3748;
        text-align: left;
    }}
    td {{ padding: 7px 10px; border-bottom: 1px solid #1a1f2e; font-size: 13px; vertical-align: middle; }}
    tr:hover td {{ background: #1a1f2e; }}
    .rank  {{ width: 36px; color: #4b5563; font-weight: 700; font-size: 14px; text-align: center; }}
    .pname {{ font-weight: 700; color: #f1f5f9; min-width: 160px; }}
    .team  {{ color: #9ca3af; min-width: 130px; }}
    .pos   {{ color: #6b7280; font-size: 11px; min-width: 80px; }}
    .age   {{ color: #4ade80; font-size: 12px; font-weight: 700; text-align: center; min-width: 40px; }}
    .mins  {{ color: #6b7280; font-size: 11px; text-align: right; min-width: 60px; }}
    .bar-cell {{ width: 220px; }}
    .bar-bg {{
        position: relative; background: rgba(255,255,255,0.07);
        border-radius: 4px; height: 26px; overflow: hidden;
        display: flex; align-items: center;
    }}
    .bar-fill {{ position: absolute; left: 0; top: 0; height: 100%; border-radius: 4px; opacity: 0.85; }}
    .bar-label {{ position: relative; z-index: 1; padding-left: 10px; font-size: 13px; font-weight: 800; color: #fff; }}
    </style></head><body>
    <table>
      <thead>
        <tr>
          <th>#</th><th>Jugador</th><th>Equipo</th><th>Posición</th>
          <th style="text-align:center">Edad</th>
          <th style="text-align:right">Mins</th><th>Similitud</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    </body></html>"""

    components.html(html, height=height, scrolling=True)


with tab_similar:
    st.subheader("Jugadores Similares")
    st.caption("PCA sobre métricas por 90 y porcentuales · Distancia euclídea en espacio reducido · Comparación dentro del mismo grupo de posición")

    sim_team_col = 'Team within selected timeframe' if 'Team within selected timeframe' in df.columns else 'Team'

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    sim_pos_groups = sorted(df['Position Group'].dropna().unique())
    with sim_col1:
        sim_pos = st.selectbox("Posición", sim_pos_groups, key="sim_pos")
    sim_pos_df = df[df['Position Group'] == sim_pos]
    sim_clubs = sorted(sim_pos_df[sim_team_col].dropna().unique())
    with sim_col2:
        sim_club = st.selectbox("Club", sim_clubs, key="sim_club")
    sim_club_pos_df = sim_pos_df[sim_pos_df[sim_team_col] == sim_club]
    sim_players_list = sorted(sim_club_pos_df['Player'].dropna().unique())
    with sim_col3:
        sim_player = st.selectbox("Jugador", sim_players_list, key="sim_player")

    sim_slider_col, sim_top_col = st.columns(2)
    sim_min_v = int(df['Minutes played'].min()) if 'Minutes played' in df.columns else 0
    sim_max_v = int(df['Minutes played'].max()) if 'Minutes played' in df.columns else 100
    with sim_slider_col:
        sim_min_minutes = st.slider(
            "Minutos mínimos (pool de comparación)", sim_min_v, sim_max_v,
            value=min(200, sim_max_v), key="sim_min_minutes"
        )
    with sim_top_col:
        sim_top_n = st.slider("Cantidad de jugadores a mostrar", 5, 30, 15, key="sim_top_n")

    # Pool: misma posición + mínimo de minutos
    sim_pool = df[
        (df['Position Group'] == sim_pos) &
        (df['Minutes played'] >= sim_min_minutes)
    ].copy().reset_index(drop=True)

    sim_n_pool = len(sim_pool)
    sim_player_in_pool = sim_pool[sim_pool['Player'] == sim_player]

    if sim_player_in_pool.empty:
        st.warning("El jugador no cumple el filtro de minutos mínimos. Reducí el slider.")
    elif sim_n_pool < 5:
        st.warning("El pool de comparación tiene menos de 5 jugadores. Reducí los minutos mínimos.")
    else:
        sim_results, sim_n_comp, sim_var = _compute_similarity_scores(sim_pool, sim_player)

        if sim_results is None:
            st.warning("No hay suficientes métricas disponibles para calcular similitud.")
        else:
            # Header del jugador seleccionado
            sim_player_info = sim_pool[sim_pool['Player'] == sim_player].iloc[0]
            sim_player_team = str(sim_player_info.get(sim_team_col, ''))
            sim_player_mins = int(sim_player_info.get('Minutes played', 0))
            _sim_age_raw = sim_player_info.get('Age', None)
            sim_player_age = int(_sim_age_raw) if _sim_age_raw is not None and pd.notnull(_sim_age_raw) else '—'

            st.markdown(f"""
            <div style="background:#1a1f2e; border:1px solid #2d3748; border-radius:12px;
                        padding:16px 24px; margin-bottom:16px; display:flex; align-items:center; gap:20px;">
              <div>
                <div style="font-size:1.4rem; font-weight:800; color:#f1f5f9;">{sim_player}</div>
                <div style="color:#9ca3af; font-size:0.9rem; margin-top:4px;">
                  {sim_player_team} &nbsp;·&nbsp; {sim_pos}
                  &nbsp;·&nbsp; <span style="color:#4ade80; font-weight:700;">{sim_player_age} años</span>
                  &nbsp;·&nbsp; {sim_player_mins:,} mins
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            n_sim_cols = len(_get_similarity_cols(sim_pool))
            st.caption(
                f"🔬 PCA: **{sim_n_comp} componentes** · **{sim_var:.1f}%** varianza explicada · "
                f"**{n_sim_cols}** métricas · Pool: **{sim_n_pool}** {sim_pos.lower()}s"
            )
            st.markdown("---")

            _render_similarity_table(sim_results, sim_pool, sim_team_col, sim_top_n)

            # Tarjeta descargable
            fig_card = _create_similarity_card(
                player_name=sim_player,
                player_team=sim_player_team,
                player_age=sim_player_age,
                player_pos=sim_pos,
                player_mins=sim_player_mins,
                results=sim_results,
                pool_df=sim_pool,
                team_col=sim_team_col,
                n_comp=sim_n_comp,
                var_explained=sim_var,
                top_n=sim_top_n,
                logo_path=LOGO_BLANCO,
            )
            buf_card = io.BytesIO()
            fig_card.savefig(buf_card, format='png', dpi=180, bbox_inches='tight',
                             facecolor=fig_card.get_facecolor())
            plt.close(fig_card)
            st.download_button(
                "⬇️ Descargar tarjeta",
                buf_card.getvalue(),
                file_name=f"similares_{sim_player.replace(' ', '_')}.png",
                mime="image/png",
                key="dl_sim_card",
            )
            st.caption("𝕏: @marca_zonal  ·  Instagram: @marca.zonal")

# ---- Tab 6: Rankings ------------------------------------------------------
# Columnas "Total" excluidas del ranking (no son métricas de rendimiento)
_RANKING_EXCLUDE = {'Age', 'Height', 'Weight'}

_TOTAL_COLS = sorted([
    c for c in df.columns
    if not c.endswith(' per 90')
    and not c.endswith(', %')
    and c not in NON_METRIC_COLS
    and c not in _RANKING_EXCLUDE
    and pd.api.types.is_numeric_dtype(df[c])
])

_PER90_COLS = sorted([c for c in df.columns if c.endswith(' per 90')])

# Métricas permitidas en Rankings cuando se selecciona Portero:
# todas las del pentágono GK + Received passes per 90
_GK_RANKING_COLS = sorted([
    c for c in (
        list({col for cols in _GK_PENTAGON_COLS.values() for col in cols})
        + ['Received passes per 90']
    )
    if c in df.columns
])


def _render_ranking_table(ranking_df, metric_col, team_col, is_total=False):
    """Renderiza el ranking como tabla HTML con barras proporcionales al máximo."""
    max_val = ranking_df[metric_col].max()
    if max_val == 0:
        max_val = 1

    rows_html = ''
    for i, (_, row) in enumerate(ranking_df.iterrows(), start=1):
        pname = row['Player']
        team  = str(row.get(team_col, '—'))
        pos   = str(row.get('Position Group', '—'))
        val   = row[metric_col]
        val_fmt = str(int(val)) if is_total else (f"{val:.2f}" if isinstance(val, float) else str(val))
        bar_w = max(int((val / max_val) * 100), 1)

        # Color del top 3
        if i == 1:   rank_color, bar_color = '#fbbf24', '#fbbf24'
        elif i == 2: rank_color, bar_color = '#94a3b8', '#94a3b8'
        elif i == 3: rank_color, bar_color = '#b45309', '#b45309'
        else:        rank_color, bar_color = '#4b5563', '#16a34a'

        rows_html += f"""
        <tr>
          <td class="rank" style="color:{rank_color};">{i}</td>
          <td class="pname">{pname}</td>
          <td class="team">{team}</td>
          <td class="pos">{pos}</td>
          <td class="bar-cell">
            <div class="bar-bg">
              <div class="bar-fill" style="width:{bar_w}%; background:{bar_color};"></div>
              <span class="bar-label">{val_fmt}</span>
            </div>
          </td>
        </tr>"""

    n_rows = len(ranking_df)
    height = n_rows * 42 + 80

    html = f"""<!DOCTYPE html><html><head><style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Cousine', monospace; background: #0e1117; color: #b0b8c8; padding: 6px 2px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
        font-size: 10px; font-weight: 700; color: #6b7280;
        text-transform: uppercase; letter-spacing: 1px;
        padding: 8px 10px; border-bottom: 1px solid #2d3748; text-align: left;
    }}
    td {{ padding: 6px 10px; border-bottom: 1px solid #1a1f2e; font-size: 13px; vertical-align: middle; }}
    tr:hover td {{ background: #1a1f2e; }}
    .rank  {{ width: 36px; font-weight: 800; font-size: 15px; text-align: center; }}
    .pname {{ font-weight: 700; color: #f1f5f9; min-width: 160px; }}
    .team  {{ color: #9ca3af; min-width: 130px; }}
    .pos   {{ color: #6b7280; font-size: 11px; min-width: 90px; }}
    .bar-cell {{ width: 260px; }}
    .bar-bg {{
        position: relative; background: rgba(255,255,255,0.07);
        border-radius: 4px; height: 26px; overflow: hidden;
        display: flex; align-items: center;
    }}
    .bar-fill {{ position: absolute; left: 0; top: 0; height: 100%; border-radius: 4px; opacity: 0.80; }}
    .bar-label {{ position: relative; z-index: 1; padding-left: 10px; font-size: 13px; font-weight: 800; color: #fff; }}
    </style></head><body>
    <table>
      <thead>
        <tr>
          <th>#</th><th>Jugador</th><th>Equipo</th><th>Posición</th><th>Valor</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    </body></html>"""

    components.html(html, height=height, scrolling=True)


def _create_ranking_card(ranking_df, metric_col, team_col,
                         metric_label, tipo_label, pos_label, min_minutes,
                         top_n=15, logo_path=None, is_total=False):
    """Genera una figura matplotlib descargable con el ranking top-N."""
    import matplotlib.image as mpimg
    from matplotlib.patches import FancyBboxPatch

    top = ranking_df.head(top_n).copy()
    n_rows = len(top)
    max_val = top[metric_col].max() if not top.empty else 1
    if max_val == 0:
        max_val = 1

    fig_h = 3.2 + n_rows * 0.52
    fig, ax = plt.subplots(figsize=(10, fig_h), facecolor='#0e1117')
    ax.set_facecolor('#0e1117')
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, fig_h)

    y = fig_h

    # ── Header con filtros ───────────────────────────────────────────────────
    header_h = 1.1
    header_box = FancyBboxPatch((0.15, y - header_h - 0.15), 9.7, header_h,
                                boxstyle="round,pad=0.08",
                                facecolor='#1a1f2e', edgecolor='#2d3748', linewidth=1)
    ax.add_patch(header_box)
    ax.text(0.45, y - 0.35, metric_label, fontsize=17, fontweight='bold',
            color='#f1f5f9', va='top')

    # Chips de filtro
    chips = [
        (tipo_label,   '#0f2d14', '#22c55e'),
        (pos_label,    '#1a2e1a', '#4ade80'),
    ]
    if min_minutes > 0:
        chips.append((f'+{min_minutes} min', '#1a2e1a', '#4ade80'))
    cx = 0.45
    for chip_txt, bg, fg in chips:
        chip_w = len(chip_txt) * 0.095 + 0.30
        chip_box = FancyBboxPatch((cx, y - 0.88), chip_w, 0.30,
                                  boxstyle="round,pad=0.04",
                                  facecolor=bg, edgecolor='none')
        ax.add_patch(chip_box)
        ax.text(cx + chip_w / 2, y - 0.72, chip_txt,
                fontsize=8.5, color=fg, va='center', ha='center', fontweight='bold')
        cx += chip_w + 0.18

    ax.text(9.65, y - 0.35, 'MARCA ZONAL', fontsize=9, color='#6b7280',
            va='top', ha='right', fontstyle='italic')
    ax.text(9.65, y - 0.62, 'Rankings · Apertura 2026', fontsize=7.5,
            color='#4b5563', va='top', ha='right')
    y -= (header_h + 0.35)

    # ── Encabezado de columnas ───────────────────────────────────────────────
    ax.axhline(y, color='#2d3748', linewidth=0.8)
    for txt, xpos, align in [
        ('#',        0.35, 'center'),
        ('Jugador',  0.65, 'left'),
        ('Equipo',   3.80, 'left'),
        ('Posición', 6.10, 'left'),
        ('Valor',    9.65, 'right'),
    ]:
        ax.text(xpos, y - 0.08, txt.upper(), fontsize=7.5, color='#6b7280',
                fontweight='bold', va='top', ha=align)
    y -= 0.42
    ax.axhline(y + 0.22, color='#2d3748', linewidth=0.5)

    # ── Filas ────────────────────────────────────────────────────────────────
    for i, (_, row) in enumerate(top.iterrows(), start=1):
        pname = row['Player']
        team  = str(row.get(team_col, '—'))
        pos   = str(row.get('Position Group', '—'))
        val   = row[metric_col]
        val_fmt = str(int(val)) if is_total else (f"{val:.2f}" if isinstance(val, float) else str(val))
        bar_w_frac = (val / max_val)

        # Colores por posición
        if i == 1:   rank_color, bar_color = '#fbbf24', '#fbbf24'
        elif i == 2: rank_color, bar_color = '#94a3b8', '#94a3b8'
        elif i == 3: rank_color, bar_color = '#b45309', '#cd7c2f'
        else:        rank_color, bar_color = '#4b5563', '#16a34a'

        row_y = y - 0.08
        # Barra fondo
        bar_bg = FancyBboxPatch((5.95, row_y - 0.26), 3.55, 0.34,
                                boxstyle="round,pad=0.02",
                                facecolor='#1f2937', edgecolor='none')
        ax.add_patch(bar_bg)
        # Barra relleno
        bar_fill = FancyBboxPatch((5.95, row_y - 0.26), 3.55 * bar_w_frac, 0.34,
                                  boxstyle="round,pad=0.02",
                                  facecolor=bar_color, edgecolor='none', alpha=0.85)
        ax.add_patch(bar_fill)

        ax.text(0.35,  row_y, str(i),      fontsize=9,   color=rank_color, va='center', ha='center', fontweight='bold')
        ax.text(0.65,  row_y, pname[:26],  fontsize=9.5, color='#f1f5f9',  va='center', ha='left',   fontweight='bold')
        ax.text(3.80,  row_y, team[:22],   fontsize=8.5, color='#9ca3af',  va='center', ha='left')
        ax.text(6.10,  row_y, pos[:14],    fontsize=7.5, color='#6b7280',  va='center', ha='left')
        ax.text(9.65,  row_y, val_fmt,     fontsize=10,  color='#fff',     va='center', ha='right',  fontweight='bold')

        y -= 0.52
        ax.axhline(y + 0.28, color='#1a1f2e', linewidth=0.5)

    # ── Footer / branding ────────────────────────────────────────────────────
    ax.axhline(0.32, color='#2d3748', linewidth=0.8)
    ax.text(5.0, 0.22, 'MARCA ZONAL · Rankings · Portal de Datos del Fútbol Paraguayo',
            fontsize=7.5, color='#374151', va='center', ha='center', fontstyle='italic')
    ax.text(5.0, 0.07, '𝕏: @marca_zonal  ·  Instagram: @marca.zonal',
            fontsize=7.5, color='#4b5563', va='center', ha='center', fontstyle='italic')

    plt.tight_layout(pad=0.4)
    return fig


with tab_ranking:
    st.subheader("Rankings de métricas")

    rank_team_col = 'Team within selected timeframe' if 'Team within selected timeframe' in df.columns else 'Team'

    # ── Fila 1: tipo de métrica + posición (opcional) ──────────────────────
    rk_col1, rk_col2 = st.columns([1, 1])
    with rk_col2:
        rk_pos_opts = ["Todas las posiciones"] + sorted(df['Position Group'].dropna().unique())
        rk_pos = st.selectbox("Posición (opcional)", rk_pos_opts, key="rk_pos")

    _is_rk_gk = (rk_pos == "Portero")

    with rk_col1:
        if _is_rk_gk:
            rk_tipo = "Por 90"
            st.info("🥅 Portero: se muestran solo métricas del OVERALL")
        else:
            rk_tipo = st.selectbox("Tipo de métrica", ["Por 90", "Total"], key="rk_tipo")

    # ── Slider de minutos solo para Por 90 ─────────────────────────────────
    if rk_tipo == "Por 90":
        rk_min_v = int(df['Minutes played'].min()) if 'Minutes played' in df.columns else 0
        rk_max_v = int(df['Minutes played'].max()) if 'Minutes played' in df.columns else 100
        rk_min_minutes = st.slider(
            "Minutos mínimos jugados", rk_min_v, rk_max_v,
            value=min(200, rk_max_v), key="rk_min_minutes"
        )
    else:
        rk_min_minutes = 0

    # ── Selector de métrica ─────────────────────────────────────────────────
    if _is_rk_gk:
        rk_metric_cols = _GK_RANKING_COLS
    else:
        rk_metric_cols = _PER90_COLS if rk_tipo == "Por 90" else _TOTAL_COLS
    rk_metric = st.selectbox(
        "Métrica", rk_metric_cols,
        format_func=translate,
        key="rk_metric"
    )

    # ── Construir pool ──────────────────────────────────────────────────────
    rk_pool = df.copy()
    if rk_pos != "Todas las posiciones":
        rk_pool = rk_pool[rk_pool['Position Group'] == rk_pos]
    if rk_min_minutes > 0 and 'Minutes played' in rk_pool.columns:
        rk_pool = rk_pool[rk_pool['Minutes played'] >= rk_min_minutes]

    if rk_metric not in rk_pool.columns:
        st.warning("La métrica seleccionada no está disponible en los datos.")
    elif rk_pool.empty:
        st.warning("No hay jugadores que cumplan los filtros seleccionados.")
    else:
        rk_data = rk_pool[['Player', rank_team_col, 'Position Group', rk_metric]].copy()
        rk_data = rk_data.dropna(subset=[rk_metric])
        rk_data = rk_data.sort_values(rk_metric, ascending=False).reset_index(drop=True)

        n_ranked = len(rk_data)
        pos_label = rk_pos if rk_pos != "Todas las posiciones" else "todos los jugadores"
        mins_label = f" · +{rk_min_minutes} min" if rk_min_minutes > 0 else ""
        st.caption(
            f"**{translate(rk_metric)}** · {n_ranked} jugadores · {pos_label}{mins_label} · Apertura 2026"
        )
        st.markdown("---")

        _render_ranking_table(rk_data, rk_metric, rank_team_col, is_total=(rk_tipo == "Total"))

        # ── Tarjeta descargable (top 15) ────────────────────────────────────
        _rk_tipo_label  = rk_tipo
        _rk_pos_label   = rk_pos if rk_pos != "Todas las posiciones" else "Todas las posiciones"
        fig_rk_card = _create_ranking_card(
            ranking_df=rk_data,
            metric_col=rk_metric,
            team_col=rank_team_col,
            metric_label=translate(rk_metric),
            tipo_label=_rk_tipo_label,
            pos_label=_rk_pos_label,
            min_minutes=rk_min_minutes,
            top_n=15,
            logo_path=LOGO_BLANCO,
            is_total=(rk_tipo == "Total"),
        )
        buf_rk = io.BytesIO()
        fig_rk_card.savefig(buf_rk, format='png', dpi=180, bbox_inches='tight',
                            facecolor=fig_rk_card.get_facecolor())
        plt.close(fig_rk_card)
        _rk_fname = f"ranking_{translate(rk_metric).replace(' ', '_')[:30]}.png"
        st.download_button(
            "⬇️ Descargar ranking (top 15)",
            buf_rk.getvalue(),
            file_name=_rk_fname,
            mime="image/png",
            key="dl_rk_card",
        )
        st.caption("𝕏: @marca_zonal  ·  Instagram: @marca.zonal")

# ---------------------------------------------------------------------------
# Footer — contador de visitas
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(f"👁️ Visitas a la app: **{_visit_count:,}**  ·  Marca Zonal · Apertura 2026")
