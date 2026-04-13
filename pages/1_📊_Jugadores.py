import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import io
import os
import json
import urllib.request
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as _fm
from collections import defaultdict
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from utils.data_processing import load_and_process_data, process_database
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
@st.cache_data
def load_external_league(league_name: str):
    """Carga y procesa una liga externa (ARG.xlsx, BRA.xlsx, URU.xlsx, etc.).
    Retorna un DataFrame procesado, o None si el archivo no existe."""
    possible_paths = [
        os.path.join(_ROOT_DIR, 'data', f'{league_name}.xlsx'),
        os.path.join('data', f'{league_name}.xlsx'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            _df = pd.read_excel(path)
            return process_database(_df)
    return None

# Load data
# ---------------------------------------------------------------------------
try:
    df = load_and_process_data()
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# Ligas externas — solo se usan en la pestaña Similitudes
df_arg = load_external_league('ARG')
df_bra = load_external_league('BRA')
df_uru = load_external_league('URU')
df_col = load_external_league('COL')
df_ecu = load_external_league('ECU')

# Drop rows without position group
df = df.dropna(subset=['Position Group'])

# Identify metric columns (numeric only, excluding non-metric cols)
metric_columns = sorted([
    c for c in df.columns
    if c not in NON_METRIC_COLS and pd.api.types.is_numeric_dtype(df[c])
])


def _get_age_bounds(dataframe):
    if 'Age' not in dataframe.columns or dataframe.empty:
        return 0, 40
    age_vals = pd.to_numeric(dataframe['Age'], errors='coerce').dropna()
    if age_vals.empty:
        return 0, 40
    age_min = int(np.floor(age_vals.min()))
    age_max = int(np.ceil(age_vals.max()))
    if age_min >= age_max:
        age_max = age_min + 1
    return age_min, age_max


def _apply_age_filter(dataframe, age_range):
    if 'Age' not in dataframe.columns or dataframe.empty:
        return dataframe.copy()
    age_vals = pd.to_numeric(dataframe['Age'], errors='coerce')
    age_min, age_max = age_range
    return dataframe[age_vals.between(age_min, age_max, inclusive='both')].copy()

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
# Logo centrado
_hdr_l, _hdr_c, _hdr_r = st.columns([1, 2, 1])
with _hdr_c:
    st.image(LOGO_BLANCO, use_column_width=True)

st.markdown("""
<div style="text-align:center; padding: 4px 0 16px 0;">
  <p style="font-size:2.1rem; font-weight:700; color:#ffffff; margin:0 0 6px 0;
            font-family:'Poppins',sans-serif; letter-spacing:3px; text-transform:uppercase;">
    Portal de Datos
  </p>
  <p style="font-size:1.05rem; color:#9ca3af; margin:0; letter-spacing:1px;">
    Análisis de rendimiento del fútbol paraguayo · Apertura 2026
  </p>
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
tab_table, tab_xy, tab_bar, tab_pizza, tab_similar, tab_ranking, tab_swarm, tab_best11 = st.tabs(
    ["📊 Tabla de datos", "📈 Gráfico XY", "🏆 OVERALL", "🎯 Radial", "🔍 Similares", "🏅 Rankings", "🐝 Swarm", "⚽ Mejor Once"]
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
    ax.set_ylim(110, -16)
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

    fig.text(0.5, 0.1, 'X: @marca_zonal  ·  Instagram: @marca.zonal',
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

    pos_df = df[df['Position Group'] == selected_pos].copy()
    t1_age_min, t1_age_max = _get_age_bounds(pos_df)
    tab1_age_range = st.slider(
        "Rango de edad", t1_age_min, t1_age_max,
        value=(t1_age_min, t1_age_max), key=f"tab1_age_range_{selected_pos}"
    )
    pos_df = _apply_age_filter(pos_df, tab1_age_range)
    if pos_df.empty:
        st.warning("No hay jugadores que cumplan el rango de edad seleccionado.")
        players_list = []
        club_pos_df = pos_df.copy()
        selected_player_tab1 = None
    else:
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
    player_rows = club_pos_df[club_pos_df['Player'] == selected_player_tab1] if selected_player_tab1 else pd.DataFrame()
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
    xy_age_min, xy_age_max = _get_age_bounds(xy_group_df)
    xy_age_range = st.slider(
        "Rango de edad", xy_age_min, xy_age_max,
        value=(xy_age_min, xy_age_max), key="xy_age_range"
    )
    xy_group_df = _apply_age_filter(xy_group_df, xy_age_range)
    if xy_group_df.empty:
        st.warning("No hay jugadores que cumplan el rango de edad seleccionado.")
        xy_players = []
        xy_selected_player = None
    else:
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
    if xy_group_df.empty:
        pass
    elif not per90_columns:
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
            st.caption("X: @marca_zonal  ·  Instagram: @marca.zonal")

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
    pent_pos_df = df[df['Position Group'] == pent_pos].copy()
    pent_age_min, pent_age_max = _get_age_bounds(pent_pos_df)
    pent_age_range = st.slider(
        "Rango de edad", pent_age_min, pent_age_max,
        value=(pent_age_min, pent_age_max), key=f"pent_age_range_{pent_pos}"
    )
    pent_pos_df = _apply_age_filter(pent_pos_df, pent_age_range)
    if pent_pos_df.empty:
        st.warning("No hay jugadores que cumplan el rango de edad seleccionado.")
    else:
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
            pent_comparison_df = pent_pos_df[
                (pent_pos_df['Minutes played'] >= pent_min_minutes)
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
            subtitle_pent = (
                f"vs. {n_pent} {pent_pos.lower()}s · +{pent_min_minutes} min "
                f"· {pent_age_range[0]}-{pent_age_range[1]} años · Apertura 2026"
            )

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
                st.caption("X: @marca_zonal  ·  Instagram: @marca.zonal")

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

    pizza_age_min, pizza_age_max = _get_age_bounds(df)
    pizza_age_range = st.slider(
        "Rango de edad", pizza_age_min, pizza_age_max,
        value=(pizza_age_min, pizza_age_max), key="pizza_age_range"
    )

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
            pizza_group_df = _apply_age_filter(pizza_group_df, pizza_age_range)

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
                    subtitle = (
                        f"Entre {n_pizza_players} {pizza_pos_group.lower()}s +{pizza_min_minutes} min "
                        f"| {pizza_age_range[0]}-{pizza_age_range[1]} años | Apertura 2026"
                    )

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
                    st.caption("X: @marca_zonal  ·  Instagram: @marca.zonal")

# ---- Tab 5: Jugadores Similares -------------------------------------------
def _get_similarity_cols(df):
    """Columnas para el PCA de similitud: todas las per-90 y % numéricas disponibles."""
    return [
        c for c in df.columns
        if (c.endswith(' per 90') or c.endswith(', %'))
        and c not in NON_METRIC_COLS
        and pd.api.types.is_numeric_dtype(df[c])
    ]


def _compute_similarity_scores(pool_df, player_name, player_df=None):
    """
    Calcula puntajes de similitud (0–100%) vs todos los jugadores del pool.
    Si player_df se proporciona, busca al jugador en ese DF en lugar del pool.

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

    # Obtener vector del jugador (desde player_df si se proporciona, sino del pool)
    if player_df is not None:
        player_in_source = player_df[player_df['Player'] == player_name]
        if player_in_source.empty:
            return None, n_comp, var_explained
        player_metrics = player_in_source[sim_cols].fillna(0).iloc[0].values.reshape(1, -1)
        player_metrics = player_metrics[:, var_mask]
        player_scaled = scaler.transform(player_metrics)
        player_vec = pca.transform(player_scaled)[0]
    else:
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
        liga_raw = str(info['Liga'].values[0]) if ('Liga' in info.columns and not info.empty) else ''
        liga_code = liga_raw.split()[-1] if liga_raw else ''
        team_display = f"{team} [{liga_code}]" if liga_code and liga_code != 'PAR' else team

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
        ax.text(3.80, row_y, team_display[:24], fontsize=8.5, color='#9ca3af', va='center', ha='left')
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
    ax.text(5.0, 0.07, 'X: @marca_zonal  ·  Instagram: @marca.zonal',
            fontsize=7.5, color='#4b5563', va='center', ha='center', fontstyle='italic')

    plt.tight_layout(pad=0.4)
    return fig


def _render_similarity_table(results, pool_df, team_col, top_n):
    """Renderiza la tabla de similitud como HTML con barras de porcentaje."""
    _LIGA_COLORS = {
        'PAR': '#ef4444',   # rojo
        'ARG': '#38bdf8',   # celeste
        'BRA': '#34d399',   # verde
        'URU': '#60a5fa',   # azul
        'COL': '#f59e0b',   # amarillo/amber
        'ECU': '#a78bfa',   # violeta
    }
    _has_liga = 'Liga' in pool_df.columns

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
        liga  = str(player_info['Liga'].values[0]) if (_has_liga and not player_info.empty) else ''

        # Badge de liga
        liga_badge = ''
        if liga:
            badge_color = _LIGA_COLORS.get(liga, '#6b7280')
            liga_badge = (f'<span style="display:inline-block; margin-left:6px; padding:1px 6px; '
                          f'border-radius:4px; font-size:10px; font-weight:700; '
                          f'background:{badge_color}22; color:{badge_color}; '
                          f'border:1px solid {badge_color}55;">{liga}</span>')

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
          <td class="pname">{pname}{liga_badge}</td>
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
    sim_pos_df = df[df['Position Group'] == sim_pos].copy()
    sim_age_min, sim_age_max = _get_age_bounds(sim_pos_df)
    sim_age_range = st.slider(
        "Rango de edad", sim_age_min, sim_age_max,
        value=(sim_age_min, sim_age_max), key=f"sim_age_range_{sim_pos}"
    )
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

    # ── Selección de ligas ───────────────────────────────────────────────────
    st.markdown(
        "<p style='margin:10px 0 8px 0; font-size:0.9rem; color:#9ca3af;'>"
        "<b>Liga/s a comparar:</b></p>",
        unsafe_allow_html=True,
    )

    st.markdown("""
    <style>
    div[data-testid="stCheckbox"] label p {
        font-weight: 800 !important;
        letter-spacing: 0.02em;
        font-size: 0.92rem !important;
        line-height: 1.15 !important;
        white-space: normal !important;
    }
    div[data-testid="stCheckbox"]:has(input[aria-label="Paraguay"]) label p { color: #ef4444 !important; }
    div[data-testid="stCheckbox"]:has(input[aria-label="Argentina"]) label p { color: #38bdf8 !important; }
    div[data-testid="stCheckbox"]:has(input[aria-label="Brasil"]) label p { color: #34d399 !important; }
    div[data-testid="stCheckbox"]:has(input[aria-label="Uruguay"]) label p { color: #60a5fa !important; }
    div[data-testid="stCheckbox"]:has(input[aria-label="Colombia"]) label p { color: #f59e0b !important; }
    div[data-testid="stCheckbox"]:has(input[aria-label="Ecuador"]) label p { color: #a78bfa !important; }
    @media (max-width: 768px) {
        div[data-testid="stCheckbox"] label p {
            font-size: 0.82rem !important;
            line-height: 1.15 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    _ck_row1_col1, _ck_row1_col2, _ck_row1_col3 = st.columns(3)
    _ck_row2_col1, _ck_row2_col2, _ck_row2_col3 = st.columns(3)
    with _ck_row1_col1:
        sim_use_par = st.checkbox(
            "Paraguay", value=True, key="sim_use_par",
        )
    with _ck_row1_col2:
        sim_use_arg = st.checkbox(
            "Argentina", value=False, key="sim_use_arg",
            disabled=(df_arg is None),
        )
    with _ck_row1_col3:
        sim_use_bra = st.checkbox(
            "Brasil", value=False, key="sim_use_bra",
            disabled=(df_bra is None),
        )
    with _ck_row2_col1:
        sim_use_uru = st.checkbox(
            "Uruguay", value=False, key="sim_use_uru",
            disabled=(df_uru is None),
        )
    with _ck_row2_col2:
        sim_use_col = st.checkbox(
            "Colombia", value=False, key="sim_use_col",
            disabled=(df_col is None),
        )
    with _ck_row2_col3:
        sim_use_ecu = st.checkbox(
            "Ecuador", value=False, key="sim_use_ecu",
            disabled=(df_ecu is None),
        )

    # Construir el pool dinámicamente según las ligas seleccionadas
    _pool_parts = []

    # Filtros base para cada liga
    if sim_use_par:
        sim_pool_par = df[
            (df['Position Group'] == sim_pos) &
            (df['Minutes played'] >= sim_min_minutes)
        ].copy().reset_index(drop=True)
        sim_pool_par = _apply_age_filter(sim_pool_par, sim_age_range)
        sim_pool_par['Liga'] = 'PAR'
        _pool_parts.append(sim_pool_par)

    if sim_use_arg and df_arg is not None:
        _arg_filt = df_arg[
            (df_arg['Position Group'] == sim_pos) &
            (df_arg['Minutes played'] >= sim_min_minutes)
        ].copy().reset_index(drop=True)
        _arg_filt = _apply_age_filter(_arg_filt, sim_age_range)
        _arg_filt['Liga'] = 'ARG'
        _pool_parts.append(_arg_filt)

    if sim_use_bra and df_bra is not None:
        _bra_filt = df_bra[
            (df_bra['Position Group'] == sim_pos) &
            (df_bra['Minutes played'] >= sim_min_minutes)
        ].copy().reset_index(drop=True)
        _bra_filt = _apply_age_filter(_bra_filt, sim_age_range)
        _bra_filt['Liga'] = 'BRA'
        _pool_parts.append(_bra_filt)

    if sim_use_uru and df_uru is not None:
        _uru_filt = df_uru[
            (df_uru['Position Group'] == sim_pos) &
            (df_uru['Minutes played'] >= sim_min_minutes)
        ].copy().reset_index(drop=True)
        _uru_filt = _apply_age_filter(_uru_filt, sim_age_range)
        _uru_filt['Liga'] = 'URU'
        _pool_parts.append(_uru_filt)

    if sim_use_col and df_col is not None:
        _col_filt = df_col[
            (df_col['Position Group'] == sim_pos) &
            (df_col['Minutes played'] >= sim_min_minutes)
        ].copy().reset_index(drop=True)
        _col_filt = _apply_age_filter(_col_filt, sim_age_range)
        _col_filt['Liga'] = 'COL'
        _pool_parts.append(_col_filt)

    if sim_use_ecu and df_ecu is not None:
        _ecu_filt = df_ecu[
            (df_ecu['Position Group'] == sim_pos) &
            (df_ecu['Minutes played'] >= sim_min_minutes)
        ].copy().reset_index(drop=True)
        _ecu_filt = _apply_age_filter(_ecu_filt, sim_age_range)
        _ecu_filt['Liga'] = 'ECU'
        _pool_parts.append(_ecu_filt)

    # Construir el pool de comparación (puede no incluir PAR si el usuario lo excluye)
    sim_pool = pd.concat(_pool_parts, ignore_index=True) if _pool_parts else pd.DataFrame()
    sim_n_pool = len(sim_pool)

    # Obtener datos del jugador seleccionado (siempre desde PAR)
    sim_player_data = df[(df['Player'] == sim_player) & (df['Position Group'] == sim_pos)]

    if sim_player_data.empty:
        st.warning("El jugador no está disponible en el filtro de minutos/posición.")
    elif sim_n_pool < 1:
        st.warning("El pool de comparación está vacío. Seleccioná al menos una liga.")
    elif sim_n_pool < 3:
        st.warning("El pool de comparación tiene muy pocos jugadores. Reducí los minutos mínimos o agregá más ligas.")
    else:
        sim_results, sim_n_comp, sim_var = _compute_similarity_scores(sim_pool, sim_player, player_df=sim_player_data)

        if sim_results is None:
            st.warning("No hay suficientes métricas disponibles para calcular similitud.")
        else:
            # Header del jugador seleccionado (desde sus datos originales)
            sim_player_info = sim_player_data.iloc[0]
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
            _pool_ligas = sim_pool['Liga'].value_counts().to_dict() if 'Liga' in sim_pool.columns else {}
            _pool_desc = '  ·  '.join(f"{lg} {cnt}" for lg, cnt in _pool_ligas.items()) if _pool_ligas else f"{sim_n_pool}"
            st.caption(
                f"🔬 PCA: **{sim_n_comp} componentes** · **{sim_var:.1f}%** varianza explicada · "
                f"**{n_sim_cols}** métricas · Pool: **{sim_n_pool}** {sim_pos.lower()}s  "
                f"({_pool_desc}) · {sim_age_range[0]}-{sim_age_range[1]} años"
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
            st.caption("X: @marca_zonal  ·  Instagram: @marca.zonal")

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

# Versión "Por 90": métricas GK que son ratios (per 90 o %)
_GK_RANKING_COLS_PER90 = [
    c for c in _GK_RANKING_COLS
    if c.endswith(' per 90') or c.endswith(', %')
]

# Versión "Total": reemplaza " per 90" por su equivalente de conteo total,
# mantiene las métricas % y de longitud promedio tal como están.
_GK_RANKING_COLS_TOTAL = sorted(set(
    # Totales: columna base sin " per 90", si existe en df
    [c.replace(' per 90', '') for c in _GK_RANKING_COLS if c.endswith(' per 90')
     and c.replace(' per 90', '') in df.columns]
    # Porcentajes y promedios de longitud: se mantienen igual
    + [c for c in _GK_RANKING_COLS if c.endswith(', %') or not c.endswith(' per 90')]
))


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
        if is_total:
            val_num = pd.to_numeric(val, errors='coerce')
            if pd.notna(val_num):
                val_fmt = str(math.ceil(float(val_num)))
            else:
                val_fmt = str(val)
        else:
            val_fmt = f"{val:.2f}" if isinstance(val, float) else str(val)
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
        if is_total:
            val_num = pd.to_numeric(val, errors='coerce')
            if pd.notna(val_num):
                val_fmt = str(math.ceil(float(val_num)))
            else:
                val_fmt = str(val)
        else:
            val_fmt = f"{val:.2f}" if isinstance(val, float) else str(val)
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
    ax.text(5.0, 0.07, 'X: @marca_zonal  ·  Instagram: @marca.zonal',
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
        rk_tipo = st.selectbox("Tipo de métrica", ["Por 90", "Total"], key="rk_tipo")

    rk_age_source = df if rk_pos == "Todas las posiciones" else df[df['Position Group'] == rk_pos].copy()
    rk_age_min, rk_age_max = _get_age_bounds(rk_age_source)
    rk_age_range = st.slider(
        "Rango de edad", rk_age_min, rk_age_max,
        value=(rk_age_min, rk_age_max), key=f"rk_age_range_{rk_pos}_{rk_tipo}"
    )

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
        rk_metric_cols = _GK_RANKING_COLS_PER90 if rk_tipo == "Por 90" else _GK_RANKING_COLS_TOTAL
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
    rk_pool = _apply_age_filter(rk_pool, rk_age_range)
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
        age_label = f" · {rk_age_range[0]}-{rk_age_range[1]} años"
        st.caption(
            f"**{translate(rk_metric)}** · {n_ranked} jugadores · {pos_label}{mins_label}{age_label} · Apertura 2026"
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
        st.caption("X: @marca_zonal  ·  Instagram: @marca.zonal")

# ---------------------------------------------------------------------------
# Tab 7: Swarm
# ---------------------------------------------------------------------------

def _get_top5_metrics(player_data, comparison_df, metric_cols):
    """Devuelve las 5 métricas donde el jugador tiene mayor percentil."""
    scored = []
    for c in metric_cols:
        if c not in comparison_df.columns:
            continue
        val = player_data.get(c, None)
        if val is None or pd.isnull(val):
            continue
        pct = _compute_percentile(float(val), comparison_df[c])
        scored.append((c, pct, float(val)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:5]


def _create_swarm_chart(player_data, comparison_df, metrics5, player_name, team,
                        pos_label, player_age='', player_pos='', player_mins=0):
    """
    Gráfico tipo swarm: 5 paneles verticales, uno por métrica.
    metrics5: lista de 5 col names (ya seleccionadas por el usuario o auto top-5).
    """
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe

    n = len(metrics5)
    if n == 0:
        return None

    fig, axes = plt.subplots(1, n, figsize=(15, 8), facecolor='#0e1117')
    if n == 1:
        axes = [axes]

    for i, (ax, col) in enumerate(zip(axes, metrics5)):
        series = pd.to_numeric(comparison_df[col], errors='coerce').dropna()
        if col not in comparison_df.columns or len(series) == 0:
            ax.axis('off')
            continue

        pv = player_data.get(col, None)
        player_val = float(pv) if pv is not None and not pd.isnull(pv) else None

        # ── Jitter horizontal ──────────────────────────────────────────────
        rng = np.random.default_rng(seed=42 + i)
        x_all = rng.uniform(-0.30, 0.30, len(series))

        # Gradiente de color: celeste oscuro → celeste brillante
        s_min, s_max = series.min(), series.max()
        norm = (series.values - s_min) / (s_max - s_min + 1e-9)
        colors = plt.cm.Blues(0.30 + norm * 0.65)

        ax.scatter(x_all, series.values, c=colors, s=55, alpha=0.75,
                   zorder=2, linewidths=0)

        # ── Jugador seleccionado ───────────────────────────────────────────
        if player_val is not None:
            ax.scatter([0], [player_val],
                       c='#f97316', s=220, zorder=6,
                       edgecolors='#ffffff', linewidths=2.0)

            # Valor anotado a la derecha del punto
            ax.text(0.36, player_val, f"{player_val:.2f}",
                    fontsize=11.5, color='#fb923c', fontweight='bold',
                    va='center', ha='left',
                    path_effects=[pe.withStroke(linewidth=2.5, foreground='#0e1117')])

            # Posición ordinal en el pool (1º = mejor)
            n_above = int((series > player_val).sum())
            rank = n_above + 1
            rank_str = f"{rank}º"

            badge_y = s_max + (s_max - s_min) * 0.07
            ax.text(0, badge_y, rank_str,
                    fontsize=12, color='#fbbf24', fontweight='bold',
                    ha='center', va='bottom',
                    path_effects=[pe.withStroke(linewidth=2.5, foreground='#0e1117')])

        # ── Línea y etiqueta de promedio ───────────────────────────────────
        mean_val = float(series.mean())
        ax.axhline(mean_val, color='#64748b', linewidth=1.2,
                   linestyle='--', zorder=1, alpha=0.85)
        ax.text(0, mean_val, ' Promedio',
                fontsize=8.5, color='#94a3b8', va='bottom', ha='center',
                path_effects=[pe.withStroke(linewidth=2, foreground='#0e1117')])

        # ── Estilo del panel ───────────────────────────────────────────────
        ax.set_facecolor('#0e1117')
        ax.set_xlim(-0.65, 0.82)
        ax.set_xticks([])
        for spine in ['top', 'right', 'bottom']:
            ax.spines[spine].set_visible(False)
        ax.spines['left'].set_color('#374151')
        ax.spines['left'].set_linewidth(1.0)
        ax.tick_params(axis='y', colors='#6b7280', labelsize=9.5)

        # Nombre de la métrica debajo del panel
        label_es = translate(col)
        if len(label_es) > 26:
            label_es = label_es[:24] + '…'
        ax.set_xlabel(label_es, color='#cbd5e1', fontsize=10,
                      labelpad=10, fontweight='bold')

    # ── Cabecera: nombre + equipo ─────────────────────────────────────────
    fig.suptitle(
        f"{player_name}  ·  {team}",
        color='#f1f5f9', fontsize=15, fontweight='bold', y=1.03,
    )

    # Info del jugador: Edad · Posición · Minutos
    info_parts = []
    if player_age:
        info_parts.append(f"{player_age} años")
    if player_pos:
        info_parts.append(str(player_pos))
    if player_mins:
        info_parts.append(f"{int(player_mins)} min")
    info_line = '  ·  '.join(info_parts) if info_parts else pos_label
    fig.text(0.5, 0.995, info_line,
             color='#94a3b8', fontsize=10.5, ha='center', va='top')

    # Subtítulo con pool
    fig.text(0.5, 0.968, f"Por 90 min  ·  {pos_label}",
             color='#64748b', fontsize=9.5, ha='center', va='top')

    # ── Branding redes sociales (esquina superior derecha) ─────────────────
    fig.text(0.99, 1.02,
             "X @marca_zonal   |   Instagram @marca.zonal",
             color='#e2e8f0', fontsize=10, fontweight='bold',
             ha='right', va='bottom',
             path_effects=[pe.withStroke(linewidth=2, foreground='#0e1117')])

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig


with tab_swarm:
    st.subheader("🐝 Swarm")
    st.caption("Distribución de métricas del jugador vs. su grupo posicional.")

    sw_team_col = ('Team within selected timeframe'
                   if 'Team within selected timeframe' in df.columns else 'Team')

    # ── Filtros jugador ───────────────────────────────────────────────────
    sw_c1, sw_c2, sw_c3 = st.columns([1, 1, 1])

    with sw_c1:
        sw_pos_opts = sorted(df['Position Group'].dropna().unique())
        sw_pos = st.selectbox("Posición", sw_pos_opts, key="sw_pos")

    sw_pos_df = df[df['Position Group'] == sw_pos].copy()
    sw_age_min, sw_age_max = _get_age_bounds(sw_pos_df)
    sw_age_range = st.slider(
        "Rango de edad", sw_age_min, sw_age_max,
        value=(sw_age_min, sw_age_max), key=f"sw_age_range_{sw_pos}"
    )
    sw_pos_df = _apply_age_filter(sw_pos_df, sw_age_range)
    if sw_pos_df.empty:
        st.warning("No hay jugadores que cumplan el rango de edad seleccionado.")
        sw_player = None
        sw_club_df = sw_pos_df.copy()
    else:
        with sw_c2:
            sw_club_opts = sorted(sw_pos_df[sw_team_col].dropna().unique())
            sw_club = st.selectbox("Club", sw_club_opts, key="sw_club")

        sw_club_df = sw_pos_df[sw_pos_df[sw_team_col] == sw_club]

        with sw_c3:
            sw_player_opts = sorted(sw_club_df['Player'].dropna().unique())
            if not sw_player_opts:
                st.warning("No hay jugadores para este filtro.")
                sw_player = None
            else:
                sw_player = st.selectbox("Jugador", sw_player_opts, key="sw_player")

    # ── Slider de minutos mínimos ─────────────────────────────────────────
    if 'Minutes played' in sw_pos_df.columns and len(sw_pos_df) > 0:
        _sw_mp_min = int(sw_pos_df['Minutes played'].min())
        _sw_mp_max = int(sw_pos_df['Minutes played'].max())
        if _sw_mp_min >= _sw_mp_max:
            _sw_mp_max = _sw_mp_min + 1
        sw_min_min = st.slider(
            "Minutos mínimos del pool (percentiles)",
            _sw_mp_min, _sw_mp_max,
            value=min(200, _sw_mp_max),
            key="sw_min_minutes",
        )
    else:
        sw_min_min = 0

    # Pool de comparación
    sw_comparison_df = sw_pos_df[sw_pos_df['Minutes played'] >= sw_min_min].copy() \
        if 'Minutes played' in sw_pos_df.columns else sw_pos_df.copy()

    # Métricas disponibles para este grupo posicional
    if sw_pos == 'Portero':
        sw_metric_cols = [c for c in _GK_RANKING_COLS_PER90 if c in sw_comparison_df.columns]
    else:
        sw_metric_cols = [c for c in _PER90_COLS if c in sw_comparison_df.columns]

    if sw_player and not sw_comparison_df.empty and sw_metric_cols:
        sw_player_rows = sw_pos_df[sw_pos_df['Player'] == sw_player]

        if sw_player_rows.empty:
            st.warning("No se encontraron datos para el jugador seleccionado.")
        else:
            sw_player_data = sw_player_rows.iloc[0]
            sw_team_name   = str(sw_player_data.get(sw_team_col, ''))
            _sw_player_mins = float(sw_player_data.get('Minutes played', 0) or 0)

            if _sw_player_mins < sw_min_min:
                st.warning(
                    f"⚠️ **{sw_player}** tiene **{int(_sw_player_mins)} min** jugados, "
                    f"por debajo del umbral de **{sw_min_min} min**. "
                    "Reducí el slider para incluirlo en el análisis."
                )
            else:
                # Calcular top-5 automático (para defaults y modo auto)
                sw_auto_top5 = _get_top5_metrics(
                    sw_player_data, sw_comparison_df, sw_metric_cols)
                sw_auto_cols = [c for c, _, _ in sw_auto_top5]

                st.markdown("---")

                # ── Toggle auto / manual ──────────────────────────────────
                sw_auto = st.checkbox(
                    "✨ Sugerir las 5 mejores estadísticas automáticamente",
                    value=True, key="sw_auto",
                )

                if sw_auto:
                    sw_selected_cols = sw_auto_cols
                else:
                    # 5 selectboxes manuales (default = top-5 auto)
                    st.caption("Elegí manualmente las 5 métricas a visualizar:")
                    sw_sel_cols_row = st.columns(5)
                    sw_selected_cols = []
                    for _idx, _scol in enumerate(sw_sel_cols_row):
                        _default_col = sw_auto_cols[_idx] if _idx < len(sw_auto_cols) else sw_metric_cols[0]
                        _default_idx = sw_metric_cols.index(_default_col) if _default_col in sw_metric_cols else 0
                        _chosen = _scol.selectbox(
                            f"Métrica {_idx + 1}",
                            sw_metric_cols,
                            index=_default_idx,
                            format_func=translate,
                            key=f"sw_metric_{_idx}",
                        )
                        sw_selected_cols.append(_chosen)

                # ── Datos del jugador para el header del gráfico ──────────
                sw_age  = sw_player_data.get('Age', '')
                sw_orig_pos = sw_player_data.get('Position', '')
                sw_mins_val = int(_sw_player_mins)

                # Construir lista final (col, rank, val) para el gráfico
                sw_metrics5 = []
                for c in sw_selected_cols:
                    pv = sw_player_data.get(c, None)
                    if pv is not None and not pd.isnull(pv):
                        sw_metrics5.append(c)
                    else:
                        sw_metrics5.append(c)   # igual lo pasamos; el gráfico lo maneja

                n_comp = len(sw_comparison_df)
                st.caption(
                    f"Pool: **{n_comp} {sw_pos.lower()}s** · +{sw_min_min} min "
                    f"· {sw_age_range[0]}-{sw_age_range[1]} años · Apertura 2026"
                )

                _, col_center, _ = st.columns([0.3, 9.4, 0.3])
                with col_center:
                    fig_sw = _create_swarm_chart(
                        sw_player_data, sw_comparison_df, sw_metrics5,
                        sw_player, sw_team_name, sw_pos,
                        player_age=str(sw_age) if sw_age else '',
                        player_pos=str(sw_orig_pos),
                        player_mins=sw_mins_val,
                    )
                    if fig_sw:
                        st.pyplot(fig_sw)

                        buf_sw = io.BytesIO()
                        fig_sw.savefig(buf_sw, format='png', dpi=180,
                                       bbox_inches='tight',
                                       facecolor=fig_sw.get_facecolor())
                        plt.close(fig_sw)
                        _sw_fname = f"swarm_{sw_player.replace(' ', '_')[:25]}.png"
                        st.download_button(
                            "⬇️ Descargar gráfico",
                            buf_sw.getvalue(),
                            file_name=_sw_fname,
                            mime="image/png",
                            key="dl_sw",
                        )
                        st.caption("X: @marca_zonal  ·  Instagram: @marca.zonal")


# ---- Tab 8: Mejor Once -----------------------------------------------------
# Colores por slot de posición exacta
_B11_POS_COLORS = {
    'GK':  '#f59e0b',  # ámbar
    'LB':  '#06b6d4',  # cian
    'LCB': '#3b82f6',  # azul
    'RCB': '#3b82f6',  # azul
    'RB':  '#06b6d4',  # cian
    'MID': '#8b5cf6',  # violeta
    'LW':  '#10b981',  # verde
    'RW':  '#10b981',  # verde
    'CF':  '#ef4444',  # rojo
}

_B11_POS_LABEL = {
    'GK': 'GK', 'LB': 'LB', 'LCB': 'LCB',
    'RCB': 'RCB', 'RB': 'RB',
    'MID': 'VOL', 'LW': 'EXT', 'RW': 'EXT', 'CF': 'CF',
}

# Posiciones exactas que pertenecen a cada slot
_B11_POS_MAP = {
    'GK':  {'GK'},
    'LB':  {'LB', 'LWB'},
    'LCB': {'LCB'},
    'RCB': {'RCB'},
    'RB':  {'RB', 'RWB'},
    'MID': {'DMF', 'LDMF', 'RDMF', 'LCMF', 'LAMF', 'RAMF', 'AMF'},
    'LW':  {'LW', 'LWF'},
    'RW':  {'RW', 'RWF'},
    'CF':  {'CF'},
}

# Cuántos jugadores seleccionar por slot
_B11_N_SLOTS = {
    'GK': 1, 'LB': 1, 'LCB': 1, 'RCB': 1, 'RB': 1,
    'MID': 2, 'LW': 1, 'RW': 1, 'CF': 2,
}

_B11_ROLE_METRICS = {
    'Portero': [
        ('Save rate, %', 1.4), ('Prevented goals per 90', 1.3),
        ('Conceded goals per 90', 1.2), ('xG against per 90', 1.0),
        ('Exits per 90', 0.9), ('Aerial duels won, %', 0.8),
        ('Accurate passes, %', 0.8), ('Accurate long passes, %', 0.8),
        ('Accurate progressive passes, %', 0.7),
    ],
    'Central': [
        ('Defensive duels won, %', 1.4), ('Aerial duels won, %', 1.3),
        ('Interceptions per 90', 1.2), ('Successful defensive actions per 90', 1.2),
        ('Shots blocked per 90', 0.9), ('Accurate passes per 90', 0.9),
        ('Accurate progressive passes per 90', 0.8), ('Accurate passes to final third per 90', 0.7),
    ],
    'Lateral': [
        ('Defensive duels won, %', 1.2), ('Interceptions per 90', 1.0),
        ('Successful defensive actions per 90', 1.0), ('Aerial duels won, %', 0.7),
        ('Accurate passes per 90', 0.8), ('Accurate progressive passes per 90', 1.1),
        ('Accurate passes to final third per 90', 1.0), ('Crosses per 90', 1.0),
        ('Accurate crosses, %', 1.0), ('Progressive runs per 90', 1.2),
    ],
    'Volante Central': [
        ('Accurate passes per 90', 1.3), ('Accurate forward passes per 90', 1.0),
        ('Accurate progressive passes per 90', 1.2), ('Accurate passes to final third per 90', 1.1),
        ('Received passes per 90', 0.9), ('Interceptions per 90', 1.0),
        ('Defensive duels won, %', 0.9), ('Successful defensive actions per 90', 0.9),
        ('Progressive runs per 90', 0.9), ('Shot assists per 90', 0.9),
        ('Key passes per 90', 1.0),
    ],
    'Extremo': [
        ('Goals per 90', 1.2), ('Shots on target per 90', 1.0),
        ('Assists per 90', 1.1), ('Shot assists per 90', 1.0),
        ('Key passes per 90', 0.9), ('Dribbles won per 90', 1.2),
        ('Successful dribbles, %', 1.0), ('Touches in box per 90', 1.0),
        ('Progressive runs per 90', 1.1), ('Accurate crosses, %', 0.8),
        ('Accurate passes to penalty area per 90', 0.9),
    ],
    'Delantero': [
        ('Goals per 90', 1.4), ('Non-penalty goals per 90', 1.2),
        ('xG per 90', 1.1), ('Shots per 90', 1.0),
        ('Shots on target per 90', 1.2), ('Goal conversion, %', 0.9),
        ('Touches in box per 90', 1.0), ('Aerial duels won, %', 0.8),
        ('Assists per 90', 0.7), ('Shot assists per 90', 0.7),
        ('Offensive duels won, %', 0.9),
    ],
}

_B11_LOWER_IS_BETTER = {'Conceded goals per 90', 'xG against per 90'}


def _compute_best_eleven_score(row, comparison_df, metric_weights):
    weighted_scores = []
    total_weight = 0.0
    for metric, weight in metric_weights:
        if metric not in comparison_df.columns or metric not in row.index:
            continue
        val = row.get(metric, None)
        if val is None or pd.isnull(val):
            continue
        pct = _compute_percentile(float(val), comparison_df[metric])
        if metric in _B11_LOWER_IS_BETTER:
            pct = max(0, 99 - pct)
        weighted_scores.append(pct * weight)
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return round(float(sum(weighted_scores) / total_weight), 1)


def _compute_best_eleven(df, min_minutes=200):
    """Selecciona el mejor once por posición exacta usando promedio de percentiles."""
    df_filt = df[df['Minutes played'] >= min_minutes].copy()
    team_col = ('Team within selected timeframe'
                if 'Team within selected timeframe' in df.columns else 'Team')

    # 1. Calcular PUNTAJE de cada jugador vs su Position Group
    all_scores = {}
    for pos_group in df_filt['Position Group'].dropna().unique():
        metric_weights = _B11_ROLE_METRICS.get(pos_group)
        if not metric_weights:
            continue
        pos_df = df_filt[df_filt['Position Group'] == pos_group]
        for _, row in pos_df.iterrows():
            avg_pct = _compute_best_eleven_score(row, pos_df, metric_weights)
            all_scores[row['Player']] = {
                'name':     row['Player'],
                'puntaje':  avg_pct,
                'club':     str(row.get(team_col, '—')),
                'age':      (int(row['Age']) if 'Age' in row.index
                             and pd.notnull(row['Age']) else '—'),
                'position': str(row.get('Position', '')),
                'position_group': pos_group,
            }

    # 2. Seleccionar los mejores por slot de posición exacta
    def _best_for_slot(slot_key):
        pos_set = _B11_POS_MAP[slot_key]
        n       = _B11_N_SLOTS[slot_key]
        cands   = [v for v in all_scores.values() if v['position'] in pos_set]
        cands.sort(key=lambda x: x['puntaje'], reverse=True)
        return cands[:n]

    return {slot: _best_for_slot(slot) for slot in _B11_POS_MAP}


def _draw_best_eleven_fig(best_eleven, min_minutes, season_label="Apertura 2026", logo_path=None):
    """Dibuja la cancha con el mejor once — todos con tarjeta, layout compacto.
    y=0 → arriba (ataque), y=105 → abajo (defensa), ylim invertido."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Arc, Circle
    import matplotlib.patheffects as pe
    import matplotlib.image as mpimg

    PW = 68.0
    PH = 105.0

    # ── Coordenadas (x, y) de cada slot ──────────────────────────────────────
    # Filas: CF y=18, LW/RW y=36, MID y=54, DEF y=72, GK y=92
    # Tarjeta (ch=8): cy0 = py - dot_r - gap - ch = py - 12
    # Espacio entre tarjeta inferior de una fila y tarjeta superior de la siguiente: 10 u
    _B11_COORDS = {
        'CF':  [(21.0, 17.0), (47.0, 17.0)],
        'LW':  [( 7.0, 34.5)],
        'RW':  [(61.0, 34.5)],
        'MID': [(21.0, 52.0), (47.0, 52.0)],
        'LB':  [( 8.0, 72.0)],
        'LCB': [(23.0, 74.0)],
        'RCB': [(45.0, 74.0)],
        'RB':  [(60.0, 72.0)],
        'GK':  [(34.0, 93.0)],
    }

    # Parámetros de tarjeta
    dot_r = 4.0   # Aumentado de 3.1 para círculos más grandes
    cw    = 14.2
    ch    = 9.2
    gap   = 1.6

    fig = plt.figure(figsize=(12.2, 14.8), facecolor='#0b1220')

    # ── Título ────────────────────────────────────────────────────────────────
    ax_t = fig.add_axes([0, 0.93, 1, 0.07])
    ax_t.set_facecolor('#0b1220')
    ax_t.axis('off')
    ax_t.text(0.5, 0.75, 'MEJOR ONCE', fontsize=24, fontweight='bold',
              color='#f8fafc', ha='center', va='center')
    ax_t.text(0.5, 0.18,
              f'Apertura 2026  ·  Mínimo {min_minutes} min  ·  Ranking por percentil promedio',
              fontsize=9, color='#0b1220', ha='center', va='center')
    ax_t.text(0.5, 0.18,
              f'{season_label}  ·  Mínimo {min_minutes} min  ·  Ranking por percentil promedio',
              fontsize=10, color='#94a3b8', ha='center', va='center')

    # ── Cancha ────────────────────────────────────────────────────────────────
    ax = fig.add_axes([0.035, 0.04, 0.93, 0.885])
    ax.set_facecolor('#0b1220')
    ax.set_xlim(-4, PW + 4)
    ax.set_ylim(110, -16)
    ax.set_ylim(109, -14)   # invertido: y pequeño → arriba (ataque)
    ax.axis('off')

    lc, la, lw = 'white', 0.38, 1.1
    lc, la, lw = '#e2e8f0', 0.42, 1.3

    # Franjas de césped
    sh = PH / 10
    for i in range(10):
        ax.add_patch(plt.Rectangle(
            (0, i * sh), PW, sh,
            facecolor='#22c55e', alpha=0.07 if i % 2 == 0 else 0.035, zorder=0))
    ax.add_patch(plt.Rectangle((0, 0), PW, PH, facecolor='#0f3b2e', alpha=0.28, zorder=0))

    # Borde cancha
    ax.plot([0, PW, PW, 0, 0], [0, 0, PH, PH, 0],
            color=lc, alpha=la, lw=lw)

    # Línea central
    cy_mid = PH / 2
    ax.plot([0, PW], [cy_mid, cy_mid], color=lc, alpha=la, lw=lw * 0.8)
    ax.add_patch(Circle((PW / 2, cy_mid), 9.15,
                         color=lc, fill=False, alpha=la, lw=lw * 0.8))
    ax.plot(PW / 2, cy_mid, 'o', color=lc, alpha=la, ms=2)

    # Áreas penales
    pa_w, pa_h = 40.32, 16.5
    pa_x = (PW - pa_w) / 2
    pb   = PH
    ax.plot([pa_x, pa_x + pa_w, pa_x + pa_w, pa_x, pa_x],
            [0, 0, pa_h, pa_h, 0], color=lc, alpha=la, lw=lw * 0.8)
    ax.plot([pa_x, pa_x + pa_w, pa_x + pa_w, pa_x, pa_x],
            [pb, pb, pb - pa_h, pb - pa_h, pb], color=lc, alpha=la, lw=lw * 0.8)

    # Áreas chicas
    ga_w, ga_h = 18.32, 5.5
    ga_x = (PW - ga_w) / 2
    ax.plot([ga_x, ga_x + ga_w, ga_x + ga_w, ga_x, ga_x],
            [0, 0, ga_h, ga_h, 0], color=lc, alpha=la, lw=lw * 0.8)
    ax.plot([ga_x, ga_x + ga_w, ga_x + ga_w, ga_x, ga_x],
            [pb, pb, pb - ga_h, pb - ga_h, pb], color=lc, alpha=la, lw=lw * 0.8)

    # Porterías
    gw, gd = 7.32, 2.5
    gx = (PW - gw) / 2
    ax.plot([gx, gx + gw, gx + gw, gx, gx],
            [-gd, -gd, 0, 0, -gd], color=lc, alpha=la * 1.2, lw=lw)
    ax.plot([gx, gx + gw, gx + gw, gx, gx],
            [pb + gd, pb + gd, pb, pb, pb + gd], color=lc, alpha=la * 1.2, lw=lw)

    # Puntos de penal y arcos
    ax.plot(PW / 2, 11,       'o', color=lc, alpha=la, ms=2)
    ax.plot(PW / 2, pb - 11,  'o', color=lc, alpha=la, ms=2)
    ax.add_patch(Arc((PW / 2, pa_h), 18.3, 18.3,
                     angle=0, theta1=38, theta2=142, color=lc, alpha=la, lw=lw * 0.8))
    ax.add_patch(Arc((PW / 2, pb - pa_h), 18.3, 18.3,
                     angle=0, theta1=218, theta2=322, color=lc, alpha=la, lw=lw * 0.8))

    # ── Jugadores — todos con tarjeta ─────────────────────────────────────────
    for slot, coords in _B11_COORDS.items():
        players = best_eleven.get(slot, [])
        col     = _B11_POS_COLORS[slot]
        lbl     = _B11_POS_LABEL[slot]

        for i, (px, py) in enumerate(coords):
            # Punto de posición
            ax.plot(px, py, 'o', color=col, ms=dot_r * 6.2,
                    zorder=9, alpha=0.92,
                    markeredgecolor='white', markeredgewidth=2.8)
            ax.text(px, py, lbl, fontsize=12.4, fontweight='bold',
                    color='white', ha='center', va='center', zorder=10)

            if i >= len(players):
                continue

            p       = players[i]
            name    = p['name'][:22]
            club    = p['club'][:22]
            age     = str(p['age'])
            puntaje = p['puntaje']

            # Tarjeta encima del punto (cy0 = top-left y del rectángulo)
            cy0 = py - dot_r - gap - ch
            cx0 = max(0.0, min(px - cw / 2, PW - cw))
            cx  = cx0 + cw / 2

            # Fondo tarjeta
            ax.add_patch(FancyBboxPatch(
                (cx0, cy0), cw, ch,
                boxstyle='round,pad=0.3',
                facecolor='#0f172a', edgecolor=col,
                linewidth=1.5, zorder=6, alpha=0.96,
                path_effects=[pe.withSimplePatchShadow(offset=(0, -1.2), alpha=0.25)]))
            # Barra de color superior
            ax.add_patch(FancyBboxPatch(
                (cx0, cy0), cw, 2.0,
                boxstyle='round,pad=0.2',
                facecolor=col, edgecolor='none',
                zorder=7, alpha=0.80))
            # Conector punto → tarjeta
            ax.plot([px, px], [py - dot_r, cy0 + ch],
                    color=col, alpha=0.35, lw=0.95, zorder=5)
            # Nombre
            ax.text(cx, cy0 + 3.3, name,
                    fontsize=14.0, fontweight='bold', color='#f8fafc',
                    ha='center', va='center', zorder=8,
                    path_effects=[pe.withStroke(linewidth=0.8, foreground='#0b1220')])
            # Club
            ax.text(cx, cy0 + 5.8, club,
                    fontsize=12.0, color='#cbd5e1',
                    ha='center', va='center', zorder=8)
            # Edad · PUNTAJE
            ax.text(cx, cy0 + 7.9,
                    f"{age}  ★ {puntaje:.1f}",
                    fontsize=12.0, fontweight='bold', color=col,
                    ha='center', va='center', zorder=8)

    # ── Branding ──────────────────────────────────────────────────────────────
    ax.text(PW / 2, 105,
            'X @marca_zonal   |   Instagram @marca.zonal',
            fontsize=8.5, color='#64748b', ha='center', va='bottom',
            fontstyle='italic')

    # ── Logo ──────────────────────────────────────────────────────────────────
    if logo_path and os.path.exists(logo_path):
        logo_img = mpimg.imread(logo_path)
        ax_lg = fig.add_axes([0.84, 0.94, 0.14, 0.055])
        ax_lg.imshow(logo_img)
        ax_lg.axis('off')

    return fig


with tab_best11:
    # ── Encabezado destacado ──────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 16px 22px;
        margin-bottom: 18px;
    ">
        <div style="font-size:22px; font-weight:800; color:#f1f5f9; letter-spacing:1px;">
            ⚽ MEJOR ONCE
        </div>
        <div style="font-size:13px; color:#94a3b8; margin-top:4px;">
            Selección automática por posición · Apertura 2026 · Percentil promedio por rol
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Minutos mínimos: 50% del máximo disponible, calculado automáticamente
    _b11_max_v   = int(df['Minutes played'].max()) if 'Minutes played' in df.columns else 90
    _b11_min_min = max(1, math.ceil(_b11_max_v / 2))

    b11_age_min, b11_age_max = _get_age_bounds(df)
    b11_age_range = st.slider(
        "Rango de edad", b11_age_min, b11_age_max,
        value=(b11_age_min, b11_age_max), key="b11_age_range"
    )
    b11_df = _apply_age_filter(df, b11_age_range)

    best_eleven = _compute_best_eleven(b11_df, min_minutes=_b11_min_min)

    # ── Figura (se genera una sola vez, se reutiliza para display y descarga) ──
    fig_b11     = _draw_best_eleven_fig(best_eleven, min_minutes=_b11_min_min,
                                        logo_path=LOGO_BLANCO)
    buf_b11     = io.BytesIO()
    fig_b11.savefig(buf_b11, format='png', dpi=130,
                    bbox_inches='tight', facecolor=fig_b11.get_facecolor())
    buf_b11_dl  = io.BytesIO()
    fig_b11.savefig(buf_b11_dl, format='png', dpi=200,
                    bbox_inches='tight', facecolor=fig_b11.get_facecolor())
    plt.close(fig_b11)

    st.image(buf_b11.getvalue(), use_column_width=True)

    st.download_button(
        "⬇️ Descargar imagen (alta resolución)",
        buf_b11_dl.getvalue(),
        file_name="mejor_once_apertura_2026.png",
        mime="image/png",
        key="dl_b11",
    )
    st.caption(
        f"Mínimo {_b11_min_min} min jugados · {b11_age_range[0]}-{b11_age_range[1]} años"
        f"  ·  X: @marca_zonal  ·  Instagram: @marca.zonal"
    )


# ---------------------------------------------------------------------------
# Footer — contador de visitas
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(f"👁️ Visitas a la app: **{_visit_count:,}**  ·  Marca Zonal · Apertura 2026")
