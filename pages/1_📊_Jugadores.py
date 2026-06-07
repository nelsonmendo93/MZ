import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import io
import os
import json
import base64
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
from utils.bar_chart import create_scout_report
from utils.scout_html import build_scout_html
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

SCOUT_METRIC_LABELS = {
    'Defensive duels won, %': 'Duelos def. %',
    'Aerial duels won, %': 'Juego aereo %',
    'Shots blocked per 90': 'Bloqueos',
    'Interceptions per 90': 'Intercepciones',
    'Fouls per 90': 'Faltas',
    'Goals per 90': 'Goles',
    'Shots on target per 90': 'Tiros al arco',
    'Assists per 90': 'Asistencias',
    'Dribbles won per 90': 'Regates',
    'Progressive runs per 90': 'Carreras prog.',
    'Received passes per 90': 'Recepciones',
    'Accurate passes per 90': 'Pases',
    'Key passes per 90': 'Pases clave',
    'Accurate passes to final third per 90': 'Pases 1/3',
    'Accurate progressive passes per 90': 'Pases prog.',
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
    df_par = load_and_process_data()
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# Sudamérica
df_arg = load_external_league('ARG')
df_bra = load_external_league('BRA')
df_uru = load_external_league('URU')
df_col = load_external_league('COL')
df_ecu = load_external_league('ECU')
df_chi = load_external_league('CHI')
df_per = load_external_league('PER')
df_ven = load_external_league('VEN')

# TOP 5 Europa
df_ing = load_external_league('ING')
df_ita = load_external_league('ITA')
df_ale = load_external_league('ALE')
df_esp = load_external_league('ESP')
df_fra = load_external_league('FRA')

# Torneos Internacionales
df_lib  = load_external_league('LIB')
df_sud  = load_external_league('SUD')
df_ucl  = load_external_league('UCL')
df_uel  = load_external_league('UEL')
df_uecl = load_external_league('UECL')

# Grupos de ligas — fuente de verdad para agrupación y comparación
_SA_CODES   = ['PAR', 'ARG', 'BRA', 'URU', 'COL', 'ECU', 'CHI', 'PER', 'VEN']
_EU_CODES   = ['ING', 'ITA', 'ALE', 'ESP', 'FRA']
_INTL_CODES = ['LIB', 'SUD', 'UCL', 'UEL', 'UECL']

# Mapa de ligas disponibles
_LIGA_DFS = {
    'PAR': df_par,
    'ARG': df_arg,
    'BRA': df_bra,
    'URU': df_uru,
    'COL': df_col,
    'ECU': df_ecu,
    'CHI': df_chi,
    'PER': df_per,
    'VEN': df_ven,
    'ING': df_ing,
    'ITA': df_ita,
    'ALE': df_ale,
    'ESP': df_esp,
    'FRA': df_fra,
    'LIB':  df_lib,
    'SUD':  df_sud,
    'UCL':  df_ucl,
    'UEL':  df_uel,
    'UECL': df_uecl,
}
_LIGA_LABELS = {
    'PAR': 'Paraguay',
    'ARG': 'Argentina',
    'BRA': 'Brasil',
    'URU': 'Uruguay',
    'COL': 'Colombia',
    'ECU': 'Ecuador',
    'CHI': 'Chile',
    'PER': 'Perú',
    'VEN': 'Venezuela',
    'ING': 'Premier League',
    'ITA': 'Serie A Calcio',
    'ALE': 'Bundesliga',
    'ESP': 'La Liga',
    'FRA': 'Ligue 1',
    'LIB':  'Libertadores 2026',
    'SUD':  'Sudamericana 2026',
    'UCL':  'Champions League 2025/26',
    'UEL':  'Europa League 2025/26',
    'UECL': 'Conference League 2025/26',
    'ALL_SA':   '🌎 Sudamérica (todas)',
    'ALL_EU':   '🌍 Europa (todas)',
    'ALL_INTL': '🏆 Torneos Internacionales (todos)',
}
_LIGA_TORNEO = {
    'PAR': 'Torneo Local 2026',
    'ARG': 'LPF 2026',
    'BRA': 'Serie A 2026',
    'URU': '1ra Div Uruguay 2026',
    'COL': 'Liga BetPlay 2026',
    'ECU': 'Liga Pro 2026',
    'CHI': '1ra Div Chile 2026',
    'PER': '1ra Div Perú 2026',
    'VEN': '1ra Div Venezuela 2026',
    'ING': 'Premier League 2025/26',
    'ITA': 'Serie A Calcio 2025/26',
    'ALE': 'Bundesliga 2025/26',
    'ESP': 'La Liga 2025/26',
    'FRA': 'Ligue 1 2025/26',
    'LIB':  'Copa Libertadores 2026',
    'SUD':  'Copa Sudamericana 2026',
    'UCL':  'UEFA Champions League 2025/26',
    'UEL':  'UEFA Europa League 2025/26',
    'UECL': 'UEFA Conference League 2025/26',
    'ALL_SA':   'Fútbol Sudamericano 2026',
    'ALL_EU':   'TOP 5 Europa 2025/26',
    'ALL_INTL': 'Torneos Internacionales 2025/26',
}

# Agregar SA
_sa_parts = []
for _code in _SA_CODES:
    _ldf = _LIGA_DFS.get(_code)
    if _ldf is not None:
        _part = _ldf.copy()
        _part['Liga'] = _code
        _sa_parts.append(_part)
df_all_sa = pd.concat(_sa_parts, ignore_index=True) if _sa_parts else pd.DataFrame()
_LIGA_DFS['ALL_SA'] = df_all_sa

# Agregar EU
_eu_parts = []
for _code in _EU_CODES:
    _ldf = _LIGA_DFS.get(_code)
    if _ldf is not None:
        _part = _ldf.copy()
        _part['Liga'] = _code
        _eu_parts.append(_part)
df_all_eu = pd.concat(_eu_parts, ignore_index=True) if _eu_parts else pd.DataFrame()
_LIGA_DFS['ALL_EU'] = df_all_eu

# Agregar Torneos Internacionales
_intl_parts = []
for _code in _INTL_CODES:
    _ldf = _LIGA_DFS.get(_code)
    if _ldf is not None:
        _part = _ldf.copy()
        _part['Liga'] = _code
        _intl_parts.append(_part)
df_all_intl = pd.concat(_intl_parts, ignore_index=True) if _intl_parts else pd.DataFrame()
_LIGA_DFS['ALL_INTL'] = df_all_intl

# df_all: todas las ligas combinadas (usado en Buscador para bounds globales)
df_all = pd.concat([df_all_sa, df_all_eu, df_all_intl], ignore_index=True) if (_sa_parts or _eu_parts or _intl_parts) else pd.DataFrame()

# Ligas disponibles por grupo (individuales + agregado)
_AVAILABLE_SA = [k for k in _SA_CODES if _LIGA_DFS.get(k) is not None] + (
    ['ALL_SA'] if not df_all_sa.empty else []
)
_AVAILABLE_EU = [k for k in _EU_CODES if _LIGA_DFS.get(k) is not None] + (
    ['ALL_EU'] if not df_all_eu.empty else []
)
_AVAILABLE_INTL = [k for k in _INTL_CODES if _LIGA_DFS.get(k) is not None]
_AVAILABLE_LIGAS = _AVAILABLE_SA + _AVAILABLE_EU + _AVAILABLE_INTL

# Selector de liga — dos pasos: Grupo → Liga
_sel_c1, _sel_c2, _ = st.columns([1, 1, 2])
with _sel_c1:
    _grupo = st.selectbox(
        "🌍 Grupo",
        options=['Sudamérica', 'Europa', 'Torneos Internacionales'],
        key="grupo_selector",
    )
with _sel_c2:
    if _grupo == 'Sudamérica':
        _ligas_options = _AVAILABLE_SA
    elif _grupo == 'Europa':
        _ligas_options = _AVAILABLE_EU
    else:
        _ligas_options = _AVAILABLE_INTL
    liga_activa = st.selectbox(
        "🌎 Liga",
        options=_ligas_options,
        format_func=lambda k: _LIGA_LABELS[k],
        index=0,
        key="liga_activa_selector",
    )

# df activo según liga seleccionada
df = _LIGA_DFS[liga_activa].dropna(subset=['Position Group'])

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

# Pesos de métricas individuales por grupo de posición.
# ⭐ High = 3.0 | Normal = 1.0 | Bajo = 0.3
# Las métricas no listadas reciben peso 1.0 por defecto.
_POSITION_METRIC_WEIGHTS = {
    'Delantero': {
        'Goals per 90':                          3.0,
        'xG per 90':                             3.0,
        'Shots on target per 90':                2.5,
        'Non-penalty goals per 90':              2.0,
        'Touches in box per 90':                 2.0,
        'Successful attacking actions per 90':   2.0,
        'xA per 90':                             2.0,
        'Key passes per 90':                     1.5,
        'Dribbles per 90':                       1.5,
        'Aerial duels won, %':                   1.5,
        'Accurate back passes, %':               0.3,
        'Yellow cards per 90':                   0.3,
        'Red cards per 90':                      0.3,
    },
    'Extremo': {
        'Goals per 90':                          3.0,
        'xG per 90':                             3.0,
        'Shots on target per 90':                3.0,
        'Successful attacking actions per 90':   3.0,
        'xA per 90':                             3.0,
        'Key passes per 90':                     3.0,
        'Dribbles per 90':                       3.0,
        'Progressive runs per 90':               3.0,
        'Touches in box per 90':                 2.0,
        'Shot assists per 90':                   1.5,
        'Accurate crosses per 90':               1.5,
        'Successful defensive actions per 90':   0.5,
        'Accurate back passes, %':               0.3,
        'Yellow cards per 90':                   0.3,
        'Red cards per 90':                      0.3,
    },
    'Volante Central': {
        'Accurate passes, %':                    3.0,
        'Accurate progressive passes per 90':    3.0,
        'Received passes per 90':                3.0,
        'Successful defensive actions per 90':   3.0,
        'Accurate forward passes, %':            2.0,
        'Interceptions per 90':                  2.0,
        'Defensive duels won, %':                2.0,
        'Key passes per 90':                     2.0,
        'xA per 90':                             2.0,
        'Progressive runs per 90':               1.5,
        'Goals per 90':                          0.5,
        'Shots on target per 90':                0.5,
    },
    'Lateral': {
        'Successful defensive actions per 90':   3.0,
        'Defensive duels won, %':                3.0,
        'Accurate progressive passes per 90':    3.0,
        'Interceptions per 90':                  2.0,
        'Accurate crosses per 90':               2.5,
        'Successful attacking actions per 90':   2.0,
        'xA per 90':                             2.0,
        'Progressive runs per 90':               2.0,
        'Key passes per 90':                     1.5,
        'Dribbles per 90':                       1.5,
        'Goals per 90':                          0.5,
        'Yellow cards per 90':                   0.3,
        'Red cards per 90':                      0.3,
    },
    'Central': {
        'Aerial duels won, %':                   3.0,
        'Successful defensive actions per 90':   3.0,
        'Interceptions per 90':                  3.0,
        'Defensive duels won, %':                3.0,
        'Accurate passes, %':                    2.5,
        'Accurate long passes, %':               2.0,
        'Accurate progressive passes per 90':    2.0,
        'Shots blocked per 90':                  1.5,
        'Goals per 90':                          0.3,
        'Shots on target per 90':                0.3,
        'Dribbles per 90':                       0.5,
        'Yellow cards per 90':                   0.3,
        'Red cards per 90':                      0.3,
    },
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
        and c not in _GK_ONLY_METRICS
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

st.markdown(f"""
<div style="text-align:center; padding: 4px 0 16px 0;">
  <p style="font-size:2.1rem; font-weight:700; color:#ffffff; margin:0 0 6px 0;
            font-family:'Poppins',sans-serif; letter-spacing:3px; text-transform:uppercase;">
    Portal de Datos
  </p>
  <p style="font-size:1.05rem; color:#9ca3af; margin:0; letter-spacing:1px;">
    Análisis de rendimiento · {_LIGA_TORNEO.get(liga_activa, '2026')}
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
                         team, age, matches, minutes, nationality='') -> str:
    """Tarjeta completa: campo a la izquierda, nombre + stats a la derecha."""
    field_svg = _field_html(position_code)
    age_str     = str(int(age))     if age     and str(age)     != 'nan' else '—'
    matches_str = str(int(matches)) if matches and str(matches) != 'nan' else '—'
    minutes_str = str(int(minutes)) if minutes and str(minutes) != 'nan' else '—'
    nat_str     = str(nationality).strip() if nationality and str(nationality).strip() not in ('', 'nan') else '—'

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
      <div class="sitem"><div class="slabel">Nacionalidad</div>
        <div class="sval" title="{nat_str}">{nat_str}</div></div>
      <div class="sitem"><div class="slabel">Edad</div>
        <div class="sval">{age_str}</div></div>
      <div class="sitem"><div class="slabel">Partidos</div>
        <div class="sval">{matches_str}</div></div>
    </div>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_home, tab_perfil, tab_overall, tab_xy, tab_similar, tab_ranking, tab_best11, tab_query = st.tabs(
    ["🏠 Inicio", "👤 Perfil", "🏆 Overall", "📈 Gráfico XY", "🔍 Similares", "🏅 Rankings", "⚽ Mejor Once", "🔎 Buscador"]
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


def _compute_pentagon_scores(player_data, comparison_df, all_cols, position_group=None):
    """Calcula los 5 puntajes del pentágono promediando percentiles por macro-categoría.
    Si se pasa position_group, aplica pesos diferenciados por métrica según posición."""
    weights_map = _POSITION_METRIC_WEIGHTS.get(position_group, {}) if position_group else {}

    pcts_by_cat = defaultdict(list)
    wgts_by_cat = defaultdict(list)
    for c in all_cols:
        val = player_data.get(c, None)
        if pd.isnull(val):
            continue
        pv = float(val)
        pct = _compute_percentile(pv, comparison_df[c]) if c in comparison_df.columns else 0
        cat = categorize_metric(c)
        pcts_by_cat[cat].append(pct)
        wgts_by_cat[cat].append(weights_map.get(c, 1.0))

    def wavg_cats(*cats):
        vals = []
        wgts = []
        for cat in cats:
            vals.extend(pcts_by_cat.get(cat, []))
            wgts.extend(wgts_by_cat.get(cat, []))
        if not vals:
            return 0.0
        return float(np.average(vals, weights=wgts))

    atq = wavg_cats('\u26bd Goles y Remates')
    pos = wavg_cats('\u26a1 Posesi\u00f3n')
    pas = wavg_cats('\U0001f4d0 Pases', '\u2197\ufe0f Centros')
    cre = wavg_cats('\U0001f3af Creaci\u00f3n')
    def_pos = wavg_cats('\U0001f6e1\ufe0f Defensa', '\U0001f4aa Duelos')
    def_neg = wavg_cats('\U0001f4cb Disciplina')
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
                           team2='', custom_labels=None):
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

    # fig.add_axes con posición explícita: reserva 14% inferior para leyenda + branding
    fig = plt.figure(figsize=(6.5, 7.6), facecolor='#0f1117')
    ax = fig.add_axes([0.05, 0.14, 0.90, 0.84])
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

    # xlim/ylim calibrados al ratio del axes box (5.85"/6.384"=0.916) → sin slack interno
    ax.set_xlim(-1.59, 1.59)
    ax.set_ylim(-1.36, 2.12)

    # Título — nombre del jugador
    if compare_mode:
        t1 = f'{player_name} ({team})' if team else player_name
        t2 = f'{player2_name} ({team2})' if team2 else player2_name
        title_text = f'{t1}  ⚔  {t2}'
        title_fs   = 9
    else:
        title_text = player_name
        title_fs   = 14
    ax.text(0, 2.08, title_text, ha='center', va='top',
            fontsize=title_fs, fontweight='bold', color='white')

    # Equipo (solo modo individual)
    if not compare_mode:
        ax.text(0, 1.90, team, ha='center', va='top',
                fontsize=9, fontweight='bold', color='#38bdf8')

    # Subtítulo de contexto
    subtitle_y = 1.74 if not compare_mode else 1.75
    ax.text(0, subtitle_y, subtitle, ha='center', va='top',
            fontsize=7.8, color='#6b7280', wrap=True)

    # Leyenda
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
    # Leyenda anclada al borde inferior del eje (axes coords) → se ubica en el margen reservado
    leg = ax.legend(handles=legend_items, loc='upper center', ncol=2,
                    facecolor='#0f1117', edgecolor='#2d3748',
                    fontsize=7.8,
                    bbox_to_anchor=(0.5, 0.0),
                    bbox_transform=ax.transAxes)
    for txt in leg.get_texts():
        txt.set_color('#9ca3af')

    # Branding al pie de la figura, bien por debajo de la leyenda
    fig.text(0.5, 0.025, 'X: @marca_zonal  ·  Instagram: @marca.zonal',
             size=7.5, color='#6b7280', ha='center', fontstyle='italic')

    return fig


def _build_scout_categories(player_data, comparison_df):
    scout_categories = []
    scout_group_names = {
        'Defensa': 'Defensa',
        'Distribución': 'Posesion',
        'Ataque': 'Ataque',
    }

    for group_name, metric_list in PIZZA_METRICS.items():
        scout_items = []
        for metric in metric_list:
            if metric not in comparison_df.columns:
                continue
            value = pd.to_numeric(player_data.get(metric), errors='coerce')
            if pd.isna(value):
                continue
            pct = _compute_percentile(float(value), comparison_df[metric])
            scout_items.append({
                'label': SCOUT_METRIC_LABELS.get(metric, translate(metric)),
                'value': float(value),
                'pct': pct,
            })
        if scout_items:
            scout_categories.append((scout_group_names.get(group_name, group_name), scout_items))

    return scout_categories


def _build_scout_categories(player_data, comparison_df):
    scout_categories = []
    for group_name, metric_list in PIZZA_METRICS.items():
        scout_items = []
        for metric in metric_list:
            if metric not in comparison_df.columns:
                continue
            value = pd.to_numeric(player_data.get(metric), errors='coerce')
            if pd.isna(value):
                continue
            pct = _compute_percentile(float(value), comparison_df[metric])
            scout_items.append({
                'label': SCOUT_METRIC_LABELS.get(metric, translate(metric)),
                'value': float(value),
                'pct': pct,
            })
        if scout_items:
            scout_items.sort(key=lambda item: item['pct'], reverse=True)
            scout_group = 'Posesion' if group_name not in ('Defensa', 'Ataque') else group_name
            scout_categories.append((scout_group, scout_items))
    return scout_categories


def _build_scout_summary_items(player_data, team_col, selected_pos):
    def _fmt_int(value):
        if value is None or pd.isnull(value):
            return '--'
        try:
            return f"{int(float(value)):,}"
        except (TypeError, ValueError):
            return str(value)

    def _fmt_text(value, fallback='--'):
        if value is None or pd.isnull(value) or str(value).strip() == '':
            return fallback
        return str(value)

    def _translate_foot(value):
        if value is None or pd.isnull(value):
            return 'Desconocido'
        value_str = str(value).strip().lower()
        if value_str == 'right':
            return 'Diestro'
        if value_str == 'left':
            return 'Zurdo'
        if value_str in ('', 'unknown', 'nan'):
            return 'Desconocido'
        return str(value)

    return [
        ('Edad', _fmt_text(player_data.get('Age'))),
        ('Partidos', _fmt_int(player_data.get('Matches played'))),
        ('Minutos', _fmt_int(player_data.get('Minutes played'))),
        ('Pie', _translate_foot(player_data.get('Foot'))),
        ('Equipo', _fmt_text(player_data.get(team_col))),
        ('Nac.', _fmt_text(player_data.get('Birth country'))),
    ]


def _get_scout_top5_metrics(player_data, comparison_df, selected_pos):
    _is_gk = (selected_pos == 'Portero')
    metric_cols = [
        c for c in comparison_df.columns
        if c.endswith(' per 90')
        and pd.api.types.is_numeric_dtype(comparison_df[c])
        and (_is_gk or c not in _GK_ONLY_METRICS)
    ]
    scored = []
    seen = set()
    for col in metric_cols:
        if col in seen:
            continue
        seen.add(col)
        val = player_data.get(col, None)
        if val is None or pd.isnull(val):
            continue
        series = pd.to_numeric(comparison_df[col], errors='coerce').dropna()
        if series.empty:
            continue
        val_float = float(val)
        pct = _compute_percentile(val_float, series)
        if col in _GK_LOWER_IS_BETTER:
            pct = max(0, 99 - pct)
            rank = int((series < val_float).sum()) + 1
        else:
            rank = int((series > val_float).sum()) + 1
        scored.append({
            'metric': col,
            'value': val_float,
            'pct': pct,
            'rank': rank,
            'pool_size': int(len(series)),
        })
    scored.sort(key=lambda item: item['pct'], reverse=True)
    return scored[:5]


_DEFAULT_AXIS_WEIGHTS = {'ATQ': 20, 'POS': 20, 'PAS': 20, 'DEF': 20, 'CRE': 20}
_AXIS_WEIGHTS_BY_POS = {
    'Central':         {'DEF': 35, 'PAS': 20, 'POS': 20, 'CRE': 10, 'ATQ': 15},
    'Lateral':         {'DEF': 20, 'POS': 25, 'PAS': 20, 'ATQ': 20, 'CRE': 15},
    'Volante Central': {'POS': 25, 'PAS': 25, 'CRE': 15, 'DEF': 20, 'ATQ': 15},
    'Volante Ofensivo':{'CRE': 35, 'ATQ': 25, 'PAS': 20, 'POS': 15, 'DEF':  5},
    'Extremo':         {'ATQ': 30, 'CRE': 25, 'POS': 15, 'PAS': 20, 'DEF': 10},
    'Delantero':       {'ATQ': 45, 'CRE': 25, 'POS': 15, 'PAS': 10, 'DEF':  5},
}


@st.cache_data
def _compute_liga_home_ranking(source_df, min_minutes=300):
    """Calcula MARCA ZONAL SCORE para todos los jugadores outfield del df activo.
    Retorna DataFrame con columnas: Player, Team, Position Group, Score."""
    all_cols = _get_display_cols(source_df)
    pos_groups = ['Delantero', 'Extremo', 'Volante Central', 'Volante Ofensivo', 'Lateral', 'Central']
    records = []
    for pg in pos_groups:
        pg_df = source_df[
            (source_df['Position Group'] == pg) &
            (pd.to_numeric(source_df.get('Minutes played', pd.Series(dtype=float)), errors='coerce') >= min_minutes)
        ]
        if pg_df.empty:
            continue
        axis_w = _AXIS_WEIGHTS_BY_POS.get(pg, _DEFAULT_AXIS_WEIGHTS)
        total_w = sum(axis_w.values())
        for _, row in pg_df.iterrows():
            scores = _compute_pentagon_scores(row, pg_df, all_cols, position_group=pg)
            overall = sum(scores.get(k, 0) * v for k, v in axis_w.items()) / total_w
            team_col = 'Team within selected timeframe' if 'Team within selected timeframe' in row.index else 'Team'
            records.append({
                'Player': row.get('Player', ''),
                'Team': row.get(team_col, ''),
                'Position Group': pg,
                'Score': round(overall, 1),
            })
    if not records:
        return pd.DataFrame(columns=['Player', 'Team', 'Position Group', 'Score'])
    return pd.DataFrame(records).sort_values('Score', ascending=False).reset_index(drop=True)


# ---- Tab 0: Inicio -------------------------------------------------------
with tab_home:
    _home_ranking = _compute_liga_home_ranking(df)
    _team_col_home = 'Team within selected timeframe' if 'Team within selected timeframe' in df.columns else 'Team'
    _torneo_home   = _LIGA_TORNEO.get(liga_activa, '2026')
    _liga_home     = _LIGA_LABELS.get(liga_activa, liga_activa)
    _total_home    = len(df)

    # ── Hero ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
                border:1px solid rgba(34,197,94,0.18);border-radius:16px;
                padding:18px 24px;margin-bottom:24px;display:flex;
                align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
      <div>
        <div style="font-family:'Poppins',sans-serif;font-size:1.35rem;font-weight:800;
                    color:#e2e8f0;letter-spacing:1px;">{_liga_home}</div>
        <div style="font-size:0.8rem;color:#64748b;letter-spacing:1px;margin-top:2px;">
          {_torneo_home}
        </div>
      </div>
      <div style="display:flex;gap:24px;flex-wrap:wrap;">
        <div style="text-align:center;">
          <div style="font-family:'Poppins',sans-serif;font-size:1.6rem;font-weight:800;
                      color:#22c55e;">{_total_home}</div>
          <div style="font-size:0.62rem;letter-spacing:2px;color:#475569;text-transform:uppercase;">Jugadores</div>
        </div>
        <div style="text-align:center;">
          <div style="font-family:'Poppins',sans-serif;font-size:1.6rem;font-weight:800;
                      color:#38bdf8;">{df[_team_col_home].nunique() if _team_col_home in df.columns else '—'}</div>
          <div style="font-size:0.62rem;letter-spacing:2px;color:#475569;text-transform:uppercase;">Clubes</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Jugador Destacado ──────────────────────────────────────────────────
    if not _home_ranking.empty:
        _top = _home_ranking.iloc[0]
        _top_score = _top['Score']
        _top_name  = _top['Player']
        _top_team  = _top['Team']
        _top_pg    = _top['Position Group']
        _score_color = '#22c55e' if _top_score >= 70 else '#f59e0b' if _top_score >= 50 else '#ef4444'
        _bar_pct = int(_top_score)

        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.7);border:1px solid rgba(245,158,11,0.3);
                    border-radius:14px;padding:20px 24px;margin-bottom:24px;">
          <div style="font-size:0.62rem;letter-spacing:2.5px;color:#f59e0b;
                      text-transform:uppercase;font-weight:700;margin-bottom:12px;">
            ⭐ Jugador Destacado · Mayor MARCA ZONAL SCORE
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;
                      flex-wrap:wrap;gap:16px;">
            <div>
              <div style="font-family:'Poppins',sans-serif;font-size:1.5rem;font-weight:800;
                          color:#e2e8f0;">{_top_name}</div>
              <div style="font-size:0.82rem;color:#64748b;margin-top:3px;">
                {_top_team} &nbsp;·&nbsp; {_top_pg}
              </div>
            </div>
            <div style="text-align:center;">
              <div style="font-family:'Poppins',sans-serif;font-size:2.8rem;font-weight:800;
                          color:{_score_color};line-height:1;">{_top_score:.0f}</div>
              <div style="font-size:0.6rem;letter-spacing:2px;color:#475569;
                          text-transform:uppercase;">MZ Score</div>
            </div>
          </div>
          <div style="margin-top:14px;background:rgba(255,255,255,0.06);
                      border-radius:6px;height:6px;overflow:hidden;">
            <div style="width:{_bar_pct}%;height:100%;
                        background:linear-gradient(90deg,{_score_color}aa,{_score_color});
                        border-radius:6px;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── TOP 5 por posición ─────────────────────────────────────────────────
    _pos_order   = ['Delantero', 'Extremo', 'Volante Central', 'Volante Ofensivo', 'Lateral', 'Central']
    _pos_icons   = {'Delantero': '⚽', 'Extremo': '🏃', 'Volante Central': '⚙️',
                    'Volante Ofensivo': '🎨', 'Lateral': '🔁', 'Central': '🛡️'}
    _rank_colors = ['#f59e0b', '#94a3b8', '#cd7c3a', '#64748b', '#64748b']

    st.markdown("""
    <div style="font-family:'Poppins',sans-serif;font-size:1rem;font-weight:700;
                color:#94a3b8;letter-spacing:1px;margin-bottom:14px;">
      🏅 TOP 5 POR POSICIÓN · MARCA ZONAL SCORE
    </div>
    """, unsafe_allow_html=True)

    for _pg in _pos_order:
        _pg_all = _home_ranking[_home_ranking['Position Group'] == _pg]
        if _pg == 'Volante Ofensivo' and len(_pg_all) < 5:
            continue
        _pg_top = _pg_all.head(5)
        if _pg_top.empty:
            continue
        _icon = _pos_icons.get(_pg, '•')
        st.markdown(f"""
        <div style="font-size:0.7rem;letter-spacing:2px;color:#475569;
                    text-transform:uppercase;font-weight:700;margin:16px 0 8px;">
          {_icon} {_pg}
        </div>
        """, unsafe_allow_html=True)

        _cols = st.columns(5, gap="small")
        for _ci, (_, _pr) in enumerate(zip(_cols, _pg_top.itertuples())):
            _sc   = _pr.Score
            _rc   = _rank_colors[_ci] if _ci < len(_rank_colors) else '#64748b'
            _sc_c = '#22c55e' if _sc >= 70 else '#f59e0b' if _sc >= 50 else '#ef4444'
            with _cols[_ci]:
                st.markdown(f"""
                <div style="background:rgba(30,41,59,0.6);
                            border:1px solid rgba(148,163,184,0.1);
                            border-radius:10px;padding:10px 10px 8px;
                            border-top:2px solid {_rc};">
                  <div style="font-size:0.58rem;color:{_rc};font-weight:700;
                              letter-spacing:1px;margin-bottom:5px;">#{_ci+1}</div>
                  <div style="font-family:'Poppins',sans-serif;font-size:0.75rem;
                              font-weight:700;color:#e2e8f0;line-height:1.25;
                              margin-bottom:3px;word-break:break-word;">{_pr.Player}</div>
                  <div style="font-size:0.6rem;color:#64748b;margin-bottom:8px;
                              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                    {_pr.Team}</div>
                  <div style="font-family:'Poppins',sans-serif;font-size:1.1rem;
                              font-weight:800;color:{_sc_c};">{_sc:.0f}</div>
                  <div style="margin-top:5px;background:rgba(255,255,255,0.06);
                              border-radius:4px;height:3px;overflow:hidden;">
                    <div style="width:{int(_sc)}%;height:100%;
                                background:{_sc_c};border-radius:4px;opacity:0.7;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Stats Líderes ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Poppins',sans-serif;font-size:1rem;font-weight:700;
                color:#94a3b8;letter-spacing:1px;margin:28px 0 14px;">
      📊 LÍDERES DE LA LIGA
    </div>
    """, unsafe_allow_html=True)

    _min_min_stats = 300
    _df_stats = df[pd.to_numeric(df.get('Minutes played', pd.Series(dtype=float)), errors='coerce') >= _min_min_stats]

    def _stat_leader(col, label, icon, fmt='{:.2f}', higher_is_better=True):
        if col not in _df_stats.columns:
            return
        _s = pd.to_numeric(_df_stats[col], errors='coerce').dropna()
        if _s.empty:
            return None
        _idx = _s.idxmax() if higher_is_better else _s.idxmin()
        _row = _df_stats.loc[_idx]
        _val = _s[_idx]
        _name = _row.get('Player', '—')
        _team = _row.get(_team_col_home, '—')
        return {'label': label, 'icon': icon, 'name': _name, 'team': _team,
                'value': fmt.format(_val)}

    _stat_cards = [
        _stat_leader('Goals', 'Goleador', '⚽', '{:.0f}'),
        _stat_leader('Assists', 'Asistidor', '🎯', '{:.0f}'),
        _stat_leader('Duels won per 90', 'Duelos ganados/90', '💪', '{:.1f}'),
        _stat_leader('Minutes played', 'Minutos jugados', '⏱️', '{:.0f}'),
    ]
    _stat_cards = [c for c in _stat_cards if c]

    if _stat_cards:
        _scols = st.columns(len(_stat_cards), gap="small")
        for _sci, _sc_data in enumerate(_stat_cards):
            with _scols[_sci]:
                st.markdown(f"""
                <div style="background:rgba(30,41,59,0.6);
                            border:1px solid rgba(148,163,184,0.1);
                            border-radius:10px;padding:14px 14px 12px;">
                  <div style="font-size:0.62rem;letter-spacing:1.5px;color:#475569;
                              text-transform:uppercase;margin-bottom:8px;">
                    {_sc_data['icon']} {_sc_data['label']}
                  </div>
                  <div style="font-family:'Poppins',sans-serif;font-size:0.8rem;
                              font-weight:700;color:#e2e8f0;margin-bottom:2px;
                              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                    {_sc_data['name']}</div>
                  <div style="font-size:0.65rem;color:#64748b;margin-bottom:10px;
                              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                    {_sc_data['team']}</div>
                  <div style="font-family:'Poppins',sans-serif;font-size:1.4rem;
                              font-weight:800;color:#22c55e;">{_sc_data['value']}</div>
                </div>
                """, unsafe_allow_html=True)


def _get_scout_score_data(player_data, comparison_df, selected_pos):
    def _resolve_scout_weights(position_group):
        return _AXIS_WEIGHTS_BY_POS.get(position_group, _DEFAULT_AXIS_WEIGHTS)

    if selected_pos == 'Portero':
        category_scores = []
        overall_pcts = []
        current_categories = _build_scout_categories(player_data, comparison_df)
        for category_name, items in current_categories:
            if not items:
                continue
            avg_score = float(np.mean([item['pct'] for item in items]))
            category_scores.append({'code': category_name[:3].upper(), 'label': category_name, 'score': avg_score})
            overall_pcts.extend([item['pct'] for item in items])
        overall_score = float(np.mean(overall_pcts)) if overall_pcts else 0.0
        return overall_score, category_scores

    all_cols = _get_display_cols(df)
    scores = _compute_pentagon_scores(player_data, comparison_df, all_cols, position_group=selected_pos)
    ordered_axes = ['ATQ', 'POS', 'PAS', 'DEF', 'CRE']
    category_scores = [
        {'code': axis, 'label': PENTAGON_LABELS_ES.get(axis, axis), 'score': float(scores.get(axis, 0))}
        for axis in ordered_axes
    ]
    weights = _resolve_scout_weights(selected_pos)
    total_weight = sum(weights.get(item['code'], 0) for item in category_scores)
    if category_scores and total_weight > 0:
        overall_score = float(sum(item['score'] * weights.get(item['code'], 0) for item in category_scores) / total_weight)
    else:
        overall_score = float(np.mean([item['score'] for item in category_scores])) if category_scores else 0.0
    return overall_score, category_scores


def _get_scout_similarity_cols(pool_df, selected_pos=''):
    _is_gk = (selected_pos == 'Portero')
    return [
        c for c in pool_df.columns
        if (c.endswith(' per 90') or c.endswith(', %'))
        and c not in NON_METRIC_COLS
        and (_is_gk or c not in _GK_ONLY_METRICS)
        and pd.api.types.is_numeric_dtype(pool_df[c])
    ]


def _compute_scout_similarity_scores(pool_df, player_name, player_df=None, selected_pos=''):
    sim_cols = _get_scout_similarity_cols(pool_df, selected_pos=selected_pos)
    if len(sim_cols) < 3:
        return None

    X_raw = pool_df[sim_cols].fillna(0).copy()
    var_mask = X_raw.var() > 0
    X_raw = X_raw.loc[:, var_mask]
    n_features = X_raw.shape[1]
    n_samples = X_raw.shape[0]
    if n_features < 2 or n_samples < 3:
        return None

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    max_comp = min(n_features, n_samples - 1, 25)
    pca_full = PCA(n_components=max_comp, random_state=42)
    pca_full.fit(X_scaled)
    cumvar = np.cumsum(pca_full.explained_variance_ratio_)
    n_comp = int(np.argmax(cumvar >= 0.85)) + 1
    n_comp = max(3, min(n_comp, max_comp))

    pca = PCA(n_components=n_comp, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    if player_df is not None:
        player_in_source = player_df[player_df['Player'] == player_name]
        if player_in_source.empty:
            return None
        player_metrics = player_in_source[sim_cols].fillna(0).iloc[0].values.reshape(1, -1)
        player_metrics = player_metrics[:, var_mask]
        player_scaled = scaler.transform(player_metrics)
        player_vec = pca.transform(player_scaled)[0]
    else:
        players_reset = pool_df['Player'].reset_index(drop=True)
        player_mask = players_reset == player_name
        if not player_mask.any():
            return None
        player_idx = int(player_mask.idxmax())
        player_vec = X_pca[player_idx]

    distances = np.sqrt(np.sum((X_pca - player_vec) ** 2, axis=1))
    max_dist = distances.max()
    similarities = (1 - distances / max_dist) * 100.0 if max_dist > 0 else np.ones(len(distances)) * 100.0

    results = pool_df[['Player']].copy().reset_index(drop=True)
    results['Similitud'] = np.round(similarities, 1)
    results = results[results['Player'] != player_name]
    results = results.sort_values('Similitud', ascending=False).reset_index(drop=True)
    return results


def _build_scout_similarity_pool(selected_pos, min_minutes, age_range):
    # Solo compara dentro del mismo grupo continental
    _same_group = _SA_CODES if liga_activa in _SA_CODES + ['ALL_SA'] else _EU_CODES
    league_sources = [
        (code, (df if code == liga_activa else _LIGA_DFS[code]))
        for code in _same_group
        if _LIGA_DFS.get(code) is not None
    ]
    pool_parts = []
    for league_code, league_df in league_sources:
        if league_df is None or league_df.empty:
            continue
        if 'Position Group' not in league_df.columns or 'Minutes played' not in league_df.columns:
            continue
        filtered = league_df[
            (league_df['Position Group'] == selected_pos) &
            (league_df['Minutes played'] >= min_minutes)
        ].copy()
        filtered = _apply_age_filter(filtered, age_range)
        if filtered.empty:
            continue
        filtered['Liga'] = league_code
        pool_parts.append(filtered)
    return pd.concat(pool_parts, ignore_index=True) if pool_parts else pd.DataFrame()


def _build_scout_similars(selected_player, selected_pos, min_minutes, age_range, player_df, top_n=5):
    sim_pool = _build_scout_similarity_pool(selected_pos, min_minutes, age_range)
    if sim_pool.empty:
        return []

    sim_results = _compute_scout_similarity_scores(sim_pool, selected_player, player_df=player_df, selected_pos=selected_pos)
    if sim_results is None or sim_results.empty:
        return []

    similars = []
    for _, row in sim_results.head(top_n).iterrows():
        player_name = row['Player']
        player_info = sim_pool[sim_pool['Player'] == player_name]
        if player_info.empty:
            continue
        info = player_info.iloc[0]
        team_col = 'Team within selected timeframe' if 'Team within selected timeframe' in info.index else 'Team'
        age_raw = info.get('Age', None)
        age_val = '—'
        if age_raw is not None and pd.notnull(age_raw):
            try:
                age_val = int(float(age_raw))
            except (TypeError, ValueError):
                age_val = str(age_raw)
        similars.append({
            'player': player_name,
            'team': str(info.get(team_col, '')),
            'age': age_val,
            'league': str(info.get('Liga', '')),
            'similarity': float(row['Similitud']),
        })
    return similars


with tab_perfil:
    # Determine team column
    team_col_tab1 = 'Team within selected timeframe'
    if team_col_tab1 not in df.columns:
        team_col_tab1 = 'Team'

    # 3 cascading dropdowns: Club → Posición → Jugador
    col_club, col_pos, col_player = st.columns(3)

    # Step 1: Club (todas las ligas / liga activa)
    if liga_activa == 'ALL' and 'Liga' in df.columns:
        _df_sel = df.copy()
        _df_sel['_club_display'] = _df_sel[team_col_tab1].astype(str) + ' [' + _df_sel['Liga'].astype(str) + ']'
        _club_col = '_club_display'
    else:
        _df_sel = df
        _club_col = team_col_tab1

    all_clubs_perfil = sorted(_df_sel[_club_col].dropna().unique())
    with col_club:
        selected_club_perfil = st.selectbox("Club", all_clubs_perfil, key="tab1_club")

    _club_df = _df_sel[_df_sel[_club_col] == selected_club_perfil].copy()

    # Age slider (sobre el club seleccionado)
    t1_age_min, t1_age_max = _get_age_bounds(_club_df)
    tab1_age_range = st.slider(
        "Rango de edad", t1_age_min, t1_age_max,
        value=(t1_age_min, t1_age_max), key=f"tab1_age_range_{selected_club_perfil}"
    )
    _club_df = _apply_age_filter(_club_df, tab1_age_range)

    # Step 2: Posición (posiciones disponibles en ese club)
    positions_in_club = sorted(_club_df['Position Group'].dropna().unique())
    if not positions_in_club:
        st.warning("No hay jugadores que cumplan los filtros.")
        players_list = []
        club_pos_df = pd.DataFrame()
        pos_df = pd.DataFrame()
        selected_pos = ''
        selected_player_tab1 = None
    else:
        with col_pos:
            selected_pos = st.selectbox("Posición", positions_in_club, key="tab1_pos")

        # pos_df = todos los jugadores de esa posición (para percentiles de comparación)
        pos_df = df[df['Position Group'] == selected_pos].copy()
        pos_df = _apply_age_filter(pos_df, tab1_age_range)

        # club_pos_df = jugadores del club en esa posición
        club_pos_df = _club_df[_club_df['Position Group'] == selected_pos].copy()

        # Step 3: Jugador
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
            comparison_df = _apply_age_filter(comparison_df, tab1_age_range)
            n_comp = len(comparison_df)
            st.caption(
                f"Percentiles vs. **{n_comp} {selected_pos.lower()}s** "
                f"con \u2265 {tab1_min_minutes} min · {_LIGA_TORNEO.get(liga_activa, '2026')}"
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
                scout_tab, table_view_tab = st.tabs(["Vista scout", "Vista tabla"])

                with scout_tab:
                    scout_categories = _build_scout_categories(player_data, comparison_df)
                    if scout_categories:
                        team_display = str(player_data.get(team_col_tab1, ''))
                        scout_subtitle = (
                            f"Entre {n_comp} {selected_pos.lower()}s +{tab1_min_minutes} min "
                            f"| {tab1_age_range[0]}-{tab1_age_range[1]} años | {_LIGA_TORNEO.get(liga_activa, '2026')}"
                        )
                        scout_summary_items = _build_scout_summary_items(player_data, team_col_tab1, selected_pos)
                        scout_top5_metrics = _get_scout_top5_metrics(player_data, comparison_df, selected_pos)
                        scout_similars = _build_scout_similars(
                            selected_player_tab1,
                            selected_pos,
                            tab1_min_minutes,
                            tab1_age_range,
                            player_rows,
                            top_n=5,
                        )
                        scout_overall_score, scout_category_scores = _get_scout_score_data(
                            player_data, comparison_df, selected_pos
                        )
                        scout_top5_metrics_html = [
                            {**item, 'metric': translate(str(item.get('metric', '')))}
                            for item in scout_top5_metrics
                        ]

                        # Pentagon chart → base64 para embed en Vista Scout
                        _is_gk_scout = (selected_pos == 'Portero')
                        if _is_gk_scout:
                            _pent_cols = _get_display_cols_gk(df)
                            _pent_scores = _compute_pentagon_scores_gk(player_data, comparison_df, _pent_cols)
                            _pent_avg = _compute_avg_pentagon_scores_gk(comparison_df, _pent_cols)
                            _pent_labels = ['REF', 'EFE', 'DIS', 'DISP', 'ALCP']
                        else:
                            _pent_cols = _get_display_cols(df)
                            _pent_scores = _compute_pentagon_scores(
                                player_data, comparison_df, _pent_cols,
                                position_group=selected_pos,
                            )
                            _pent_avg = _compute_avg_pentagon_scores(comparison_df, _pent_cols)
                            _pent_labels = None
                        _pent_subtitle = (
                            f"vs. {n_comp} {selected_pos.lower()}s · +{tab1_min_minutes} min "
                            f"· {_LIGA_TORNEO.get(liga_activa, '2026')}"
                        )
                        _fig_pent = _create_pentagon_chart(
                            _pent_scores, selected_player_tab1, team_display,
                            _pent_subtitle, avg_scores=_pent_avg, pos_label=selected_pos,
                            custom_labels=_pent_labels if _is_gk_scout else None,
                        )
                        _buf_pent = io.BytesIO()
                        _fig_pent.savefig(_buf_pent, format='png', dpi=150,
                                          bbox_inches='tight', facecolor=_fig_pent.get_facecolor())
                        plt.close(_fig_pent)
                        _buf_pent.seek(0)
                        _pentagon_b64 = base64.b64encode(_buf_pent.read()).decode('utf-8')

                        scout_html = build_scout_html(
                            player_name=selected_player_tab1,
                            player_team=team_display,
                            subtitle=scout_subtitle,
                            summary_items=scout_summary_items,
                            top_metrics=scout_top5_metrics_html,
                            similars_data=scout_similars,
                            overall_score=scout_overall_score,
                            category_scores=scout_category_scores,
                            player_position=str(player_data.get('Position', '')),
                            pentagon_img_b64=_pentagon_b64,
                        )
                        components.html(scout_html, height=1400, scrolling=True)
                        st.caption("X: @marca_zonal  ·  Instagram: @marca.zonal")
                    else:
                        st.info("No hay suficientes métricas del radial para construir la vista scout.")

                with table_view_tab:
                    _render_all_bars(categorized, cat_order, cat_colors)
            else:
                st.info("No hay métricas disponibles para mostrar.")
    elif players_list:
        st.info("Selecciona un jugador para ver sus datos.")

# ---- Tab Overall: Pentágono MARCA ZONAL SCORE ----------------------------
with tab_overall:
    ov_team_col = 'Team within selected timeframe' if 'Team within selected timeframe' in df.columns else 'Team'

    ov_col_club, ov_col_pos, ov_col_player = st.columns(3)

    if liga_activa == 'ALL' and 'Liga' in df.columns:
        _ov_df = df.copy()
        _ov_df['_club_display'] = _ov_df[ov_team_col].astype(str) + ' [' + _ov_df['Liga'].astype(str) + ']'
        _ov_club_col = '_club_display'
    else:
        _ov_df = df
        _ov_club_col = ov_team_col

    ov_all_clubs = sorted(_ov_df[_ov_club_col].dropna().unique())
    with ov_col_club:
        ov_selected_club = st.selectbox("Club", ov_all_clubs, key="overall_club")

    _ov_club_df = _ov_df[_ov_df[_ov_club_col] == ov_selected_club].copy()
    ov_age_min, ov_age_max = _get_age_bounds(_ov_club_df)
    ov_age_range = st.slider(
        "Rango de edad", ov_age_min, ov_age_max,
        value=(ov_age_min, ov_age_max), key=f"overall_age_{ov_selected_club}"
    )
    _ov_club_df = _apply_age_filter(_ov_club_df, ov_age_range)

    ov_positions = sorted(_ov_club_df['Position Group'].dropna().unique())
    if not ov_positions:
        st.warning("No hay jugadores que cumplan los filtros.")
    else:
        with ov_col_pos:
            ov_selected_pos = st.selectbox("Posición", ov_positions, key="overall_pos")

        ov_pos_df = df[df['Position Group'] == ov_selected_pos].copy()
        ov_pos_df = _apply_age_filter(ov_pos_df, ov_age_range)

        ov_club_pos_df = _ov_club_df[_ov_club_df['Position Group'] == ov_selected_pos].copy()
        ov_players = sorted(ov_club_pos_df['Player'].dropna().unique())
        with ov_col_player:
            ov_selected_player = st.selectbox("Jugador", ov_players, key="overall_player")

        _ov_mp = ov_pos_df['Minutes played'] if 'Minutes played' in ov_pos_df.columns else None
        ov_min_v = int(_ov_mp.min()) if _ov_mp is not None and len(ov_pos_df) > 0 else 0
        ov_max_v = int(_ov_mp.max()) if _ov_mp is not None and len(ov_pos_df) > 0 else 100
        if ov_min_v >= ov_max_v:
            ov_max_v = ov_min_v + 1
        ov_min_minutes = st.slider(
            "Minutos mínimos (para percentiles)", ov_min_v, ov_max_v,
            value=min(200, ov_max_v), key=f"overall_min_min_{ov_selected_pos}"
        )

        ov_player_rows = ov_club_pos_df[ov_club_pos_df['Player'] == ov_selected_player] if ov_selected_player else pd.DataFrame()
        if not ov_player_rows.empty:
            ov_player_data = ov_player_rows.iloc[0]
            _ov_mins_val = float(ov_player_data.get('Minutes played', 0) or 0)

            if _ov_mins_val < ov_min_minutes:
                st.warning(
                    f"⚠️ **{ov_selected_player}** tiene **{int(_ov_mins_val)} min**, "
                    f"por debajo del mínimo de **{ov_min_minutes} min**. Bajá el slider."
                )
            else:
                ov_comparison_df = df[
                    (df['Position Group'] == ov_selected_pos) &
                    (df['Minutes played'] >= ov_min_minutes)
                ].copy()
                ov_comparison_df = _apply_age_filter(ov_comparison_df, ov_age_range)
                ov_n_comp = len(ov_comparison_df)

                st.caption(
                    f"Percentiles vs. **{ov_n_comp} {ov_selected_pos.lower()}s** "
                    f"con ≥ {ov_min_minutes} min · {_LIGA_TORNEO.get(liga_activa, '2026')}"
                )

                ov_is_gk = (ov_selected_pos == 'Portero')
                ov_team_display = str(ov_player_data.get(ov_team_col, ''))
                ov_subtitle = (
                    f"vs. {ov_n_comp} {ov_selected_pos.lower()}s · +{ov_min_minutes} min "
                    f"· {_LIGA_TORNEO.get(liga_activa, '2026')}"
                )

                if ov_is_gk:
                    ov_pent_cols   = _get_display_cols_gk(df)
                    ov_pent_scores = _compute_pentagon_scores_gk(ov_player_data, ov_comparison_df, ov_pent_cols)
                    ov_pent_avg    = _compute_avg_pentagon_scores_gk(ov_comparison_df, ov_pent_cols)
                    ov_custom_labels = ['REF', 'EFE', 'DIS', 'DISP', 'ALCP']
                else:
                    ov_pent_cols   = _get_display_cols(df)
                    ov_pent_scores = _compute_pentagon_scores(
                        ov_player_data, ov_comparison_df, ov_pent_cols,
                        position_group=ov_selected_pos,
                    )
                    ov_pent_avg    = _compute_avg_pentagon_scores(ov_comparison_df, ov_pent_cols)
                    ov_custom_labels = None

                ov_fig = _create_pentagon_chart(
                    ov_pent_scores, ov_selected_player, ov_team_display,
                    ov_subtitle, avg_scores=ov_pent_avg, pos_label=ov_selected_pos,
                    custom_labels=ov_custom_labels,
                )

                # MARCA ZONAL SCORE
                if not ov_is_gk:
                    ov_axis_w = _AXIS_WEIGHTS_BY_POS.get(ov_selected_pos, _DEFAULT_AXIS_WEIGHTS)
                    ov_total_w = sum(ov_axis_w.values())
                    ov_mz_score = round(
                        sum(ov_pent_scores.get(k, 0) * v for k, v in ov_axis_w.items()) / ov_total_w, 1
                    )
                    _ov_sc_col = '#22c55e' if ov_mz_score >= 70 else '#f59e0b' if ov_mz_score >= 50 else '#ef4444'
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:20px;
                                background:rgba(30,41,59,0.6);border:1px solid rgba(245,158,11,0.25);
                                border-radius:12px;padding:14px 20px;margin-bottom:16px;">
                      <div>
                        <div style="font-size:0.6rem;letter-spacing:2.5px;color:#f59e0b;
                                    text-transform:uppercase;font-weight:700;">MARCA ZONAL SCORE</div>
                        <div style="font-family:'Poppins',sans-serif;font-size:0.85rem;
                                    color:#94a3b8;margin-top:2px;">{ov_selected_player} · {ov_selected_pos}</div>
                      </div>
                      <div style="font-family:'Poppins',sans-serif;font-size:3rem;
                                  font-weight:800;color:{_ov_sc_col};line-height:1;">{ov_mz_score:.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)

                _ov_c1, _ov_c2, _ov_c3 = st.columns([1, 2, 1])
                with _ov_c2:
                    st.pyplot(ov_fig)
                plt.close(ov_fig)
        elif ov_players:
            st.info("Selecciona un jugador para ver el gráfico.")

# ---- Tab 2: XY Chart -----------------------------------------------------
with tab_xy:
    st.subheader("Gráfico XY comparativo")

    # Posición + edad
    xy_position_groups = sorted(df['Position Group'].dropna().unique())
    xy_sel1, _ = st.columns([1, 3])
    with xy_sel1:
        xy_pos_group = st.selectbox("Grupo de posición", xy_position_groups, key="xy_pos_group")
    xy_group_df = df[df['Position Group'] == xy_pos_group].copy()
    xy_age_min, xy_age_max = _get_age_bounds(xy_group_df)
    xy_age_range = st.slider(
        "Rango de edad", xy_age_min, xy_age_max,
        value=(xy_age_min, xy_age_max), key="xy_age_range"
    )
    xy_group_df = _apply_age_filter(xy_group_df, xy_age_range)

    # Only per-90 metrics — GK exclusivas solo si se selecciona Portero
    xy_is_gk = (xy_pos_group == 'Portero')
    per90_columns = sorted([
        c for c in metric_columns
        if c.endswith(' per 90')
        and (xy_is_gk or c not in _GK_ONLY_METRICS)
    ])

    if xy_group_df.empty:
        st.warning("No hay jugadores que cumplan el rango de edad seleccionado.")
    elif not per90_columns:
        st.warning("No se encontraron métricas 'por 90' en los datos.")
    else:
        # Minutos mínimos
        min_min = int(xy_group_df['Minutes played'].min()) if 'Minutes played' in xy_group_df.columns else 0
        max_min = int(xy_group_df['Minutes played'].max()) if 'Minutes played' in xy_group_df.columns else 100
        min_minutes = st.slider(
            "Minutos mínimos jugados", min_min, max_min,
            value=min(200, max_min), key="xy_min_minutes"
        )

        # Métricas X e Y
        col1, col2 = st.columns(2)
        with col1:
            x_metric = st.selectbox("Métrica eje X", per90_columns, key="xy_x",
                                     format_func=translate)
        with col2:
            y_metric = st.selectbox("Métrica eje Y", per90_columns,
                                     index=min(1, len(per90_columns) - 1),
                                     key="xy_y", format_func=translate)

        # Filtrar datos
        _xy_extra_cols = [c for c in ['Liga'] if c in xy_group_df.columns]
        xy_df = xy_group_df[xy_group_df['Minutes played'] >= min_minutes].copy()
        xy_df = xy_df[['Player', x_metric, y_metric] + _xy_extra_cols].dropna(
            subset=['Player', x_metric, y_metric]
        )

        if len(xy_df) < 2:
            st.warning("No hay suficientes datos para generar el gráfico. Probá reducir los minutos mínimos.")
        else:
            # Selectores de jugadores a etiquetar (hasta 5)
            xy_all_players = ['—'] + sorted(xy_df['Player'].dropna().unique())
            st.markdown(
                "<p style='margin:14px 0 6px 0; font-size:0.85rem; color:#9ca3af; font-weight:600;'>"
                "JUGADORES A ETIQUETAR (opcional)</p>",
                unsafe_allow_html=True,
            )
            xy_label_cols = st.columns(5)
            xy_labeled = []
            for _i in range(5):
                with xy_label_cols[_i]:
                    _sel = st.selectbox(
                        f"Jugador {_i + 1}", xy_all_players,
                        index=0, key=f"xy_label_{_i}"
                    )
                    if _sel != '—':
                        xy_labeled.append(_sel)

            fig_xy = create_xy_chart(
                xy_df, x_metric, y_metric,
                labeled_players=xy_labeled,
                x_label=translate(x_metric),
                y_label=translate(y_metric),
                logo_path=LOGO_BLANCO,
            )
            st.pyplot(fig_xy)

            buf = io.BytesIO()
            fig_xy.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                           facecolor=fig_xy.get_facecolor())
            st.download_button("⬇️ Descargar grafica", buf.getvalue(),
                               file_name="grafico_xy_marcazonal.png", mime="image/png")
            st.caption("X: @marca_zonal  ·  Instagram: @marca.zonal")

# ---- Tab 5: Jugadores Similares -------------------------------------------
def _get_similarity_cols(df, selected_pos=''):
    """Columnas para el PCA de similitud: todas las per-90 y % numéricas disponibles."""
    _is_gk = (selected_pos == 'Portero')
    return [
        c for c in df.columns
        if (c.endswith(' per 90') or c.endswith(', %'))
        and c not in NON_METRIC_COLS
        and (_is_gk or c not in _GK_ONLY_METRICS)
        and pd.api.types.is_numeric_dtype(df[c])
    ]


def _compute_similarity_scores(pool_df, player_name, player_df=None, selected_pos=''):
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
    sim_cols = _get_similarity_cols(pool_df, selected_pos=selected_pos)
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
        'PAR': '#dc2626',   # rojo intenso
        'ARG': '#14b8a6',   # teal
        'BRA': '#16a34a',   # verde fuerte
        'URU': '#2563eb',   # azul royal
        'COL': '#eab308',   # amarillo
        'ECU': '#7c3aed',   # violeta profundo
        'CHI': '#f97316',   # naranja
        'PER': '#e879f9',   # fucsia
        'VEN': '#2dd4bf',   # cian
        'LIB':  '#10b981',  # esmeralda (Libertadores)
        'SUD':  '#a78bfa',  # violeta claro (Sudamericana)
        'UCL':  '#3b82f6',  # azul Champions
        'UEL':  '#fb923c',  # naranja Europa League
        'UECL': '#22d3ee',  # cyan Conference League
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
    _LIGA_COLORS_SIM = {
        'PAR': '#dc2626', 'ARG': '#75caed', 'BRA': '#16a34a',
        'URU': '#2563eb', 'COL': '#eab308', 'ECU': '#7c3aed', 'CHI': '#f97316',
        'PER': '#e879f9', 'VEN': '#2dd4bf',
        'ING': '#e11d48', 'ITA': '#4ade80', 'ALE': '#f59e0b',
        'ESP': '#fb923c', 'FRA': '#60a5fa',
        'LIB':  '#10b981', 'SUD':  '#a78bfa',
        'UCL':  '#3b82f6', 'UEL':  '#fb923c', 'UECL': '#22d3ee',
    }
    # Checkboxes solo dentro del mismo grupo
    if liga_activa in _SA_CODES:
        _other_ligas_sim = [k for k in _AVAILABLE_SA if k not in (liga_activa, 'ALL_SA')]
    elif liga_activa in _EU_CODES:
        _other_ligas_sim = [k for k in _AVAILABLE_EU if k not in (liga_activa, 'ALL_EU')]
    elif liga_activa in _INTL_CODES:
        _other_ligas_sim = [k for k in _AVAILABLE_INTL if k not in (liga_activa, 'ALL_INTL')]
    else:
        _other_ligas_sim = []
    _active_label_sim = _LIGA_LABELS[liga_activa]

    # CSS para colores de checkboxes dinámico (excluye 'ALL' que no tiene color)
    def _ck_rule(c):
        lbl = _LIGA_LABELS[c]
        col = _LIGA_COLORS_SIM[c]
        return f'div[data-testid="stCheckbox"]:has(input[aria-label="{lbl}"]) label p {{ color: {col} !important; }}'
    _ck_css_rules = '\n'.join(_ck_rule(c) for c in _AVAILABLE_LIGAS if c in _LIGA_COLORS_SIM)
    st.markdown(f"""
    <style>
    div[data-testid="stCheckbox"] label p {{
        font-weight: 800 !important;
        letter-spacing: 0.02em;
        font-size: 0.92rem !important;
        line-height: 1.15 !important;
        white-space: normal !important;
    }}
    {_ck_css_rules}
    @media (max-width: 768px) {{
        div[data-testid="stCheckbox"] label p {{
            font-size: 0.82rem !important;
            line-height: 1.15 !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

    if liga_activa in ('ALL_SA', 'ALL_EU', 'ALL_INTL'):
        _pool_label_map = {
            'ALL_SA':   '🌎 <b>Pool Sudamericano activo</b>',
            'ALL_EU':   '🌍 <b>Pool Europeo activo</b>',
            'ALL_INTL': '🏆 <b>Pool Torneos Internacionales activo</b>',
        }
        _pool_label = _pool_label_map[liga_activa]
        st.markdown(
            f"<p style='margin:10px 0 8px 0; font-size:0.9rem; color:#9ca3af;'>"
            f"{_pool_label} — comparando contra todos los torneos del grupo.</p>",
            unsafe_allow_html=True,
        )
        _pool_all = df[
            (df['Position Group'] == sim_pos) &
            (df['Minutes played'] >= sim_min_minutes)
        ].copy().reset_index(drop=True)
        _pool_all = _apply_age_filter(_pool_all, sim_age_range)
        sim_pool = _pool_all
    else:
        st.markdown(
            "<p style='margin:10px 0 8px 0; font-size:0.9rem; color:#9ca3af;'>"
            "<b>Liga/s a comparar:</b></p>",
            unsafe_allow_html=True,
        )

        # Liga activa: siempre incluida (mostrada como fija, no desmarcable)
        _sim_liga_active_included = st.checkbox(
            _active_label_sim, value=True, key=f"sim_use_{liga_activa}",
        )

        # Otras ligas: checkboxes opcionales en grid
        _other_cols = st.columns(min(4, max(1, len(_other_ligas_sim))))
        _sim_other_selections = {}
        for _i, _code in enumerate(_other_ligas_sim):
            with _other_cols[_i % 4]:
                _lbl = _LIGA_LABELS[_code]
                _sim_other_selections[_code] = st.checkbox(
                    _lbl, value=False, key=f"sim_use_{_code}",
                    disabled=(_LIGA_DFS[_code] is None),
                )

        # Construir el pool dinámicamente
        _pool_parts = []

        if _sim_liga_active_included:
            _active_filt = df[
                (df['Position Group'] == sim_pos) &
                (df['Minutes played'] >= sim_min_minutes)
            ].copy().reset_index(drop=True)
            _active_filt = _apply_age_filter(_active_filt, sim_age_range)
            _active_filt['Liga'] = liga_activa
            _pool_parts.append(_active_filt)

        for _code, _selected in _sim_other_selections.items():
            _ldf = _LIGA_DFS[_code]
            if _selected and _ldf is not None:
                _filt = _ldf[
                    (_ldf['Position Group'] == sim_pos) &
                    (_ldf['Minutes played'] >= sim_min_minutes)
                ].copy().reset_index(drop=True)
                _filt = _apply_age_filter(_filt, sim_age_range)
                _filt['Liga'] = _code
                _pool_parts.append(_filt)

        sim_pool = pd.concat(_pool_parts, ignore_index=True) if _pool_parts else pd.DataFrame()

    sim_n_pool = len(sim_pool)

    # Obtener datos del jugador seleccionado (desde la liga activa)
    sim_player_data = df[(df['Player'] == sim_player) & (df['Position Group'] == sim_pos)]

    if sim_player_data.empty:
        st.warning("El jugador no está disponible en el filtro de minutos/posición.")
    elif sim_n_pool < 1:
        st.warning("El pool de comparación está vacío. Seleccioná al menos una liga.")
    elif sim_n_pool < 3:
        st.warning("El pool de comparación tiene muy pocos jugadores. Reducí los minutos mínimos o agregá más ligas.")
    else:
        sim_results, sim_n_comp, sim_var = _compute_similarity_scores(sim_pool, sim_player, player_df=sim_player_data, selected_pos=sim_pos)

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

            n_sim_cols = len(_get_similarity_cols(sim_pool, selected_pos=sim_pos))
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

_PER90_COLS = sorted([c for c in df.columns if c.endswith(' per 90') and c not in _GK_ONLY_METRICS])

# Métricas permitidas en Rankings cuando se selecciona Portero:
# todas las del pentágono GK + Received passes per 90
_GK_RANKING_COLS = sorted([
    c for c in (
        list({col for cols in _GK_PENTAGON_COLS.values() for col in cols})
        + ['Received passes per 90', 'Exits per 90', 'Aerial duels won, %', 'Aerial duels per 90']
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
    ax.text(9.65, y - 0.62, f'Rankings · {_LIGA_TORNEO.get(liga_activa, "2026")}', fontsize=7.5,
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
        rk_default_min = math.ceil(rk_max_v * 0.50) if rk_max_v > 0 else rk_min_v
        rk_min_minutes = st.slider(
            "Minutos mínimos jugados", rk_min_v, rk_max_v,
            value=rk_default_min, key="rk_min_minutes"
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
            f"**{translate(rk_metric)}** · {n_ranked} jugadores · {pos_label}{mins_label}{age_label} · {_LIGA_TORNEO.get(liga_activa, '2026')}"
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
    'Volante Ofensivo': [
        ('Key passes per 90', 1.4), ('Shot assists per 90', 1.3),
        ('xA per 90', 1.2), ('Assists per 90', 1.1),
        ('Goals per 90', 1.1), ('Accurate passes to final third per 90', 1.0),
        ('Accurate passes to penalty area per 90', 1.0), ('Progressive runs per 90', 1.1),
        ('Accurate progressive passes per 90', 1.0), ('Touches in box per 90', 0.9),
        ('Dribbles won per 90', 0.9),
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


def _compute_best_eleven(df, min_minutes=None):
    """Selecciona el mejor once por posición exacta usando MARCA ZONAL SCORE."""
    # Mínimo de minutos = 33% del jugador con más minutos
    if 'Minutes played' in df.columns:
        max_min = pd.to_numeric(df['Minutes played'], errors='coerce').max()
        threshold = math.ceil(max_min * 0.50) if pd.notnull(max_min) else 90
    else:
        threshold = 90
    df_filt = df[pd.to_numeric(df.get('Minutes played', pd.Series(dtype=float)), errors='coerce') >= threshold].copy()
    team_col = ('Team within selected timeframe'
                if 'Team within selected timeframe' in df.columns else 'Team')
    all_cols = _get_display_cols(df_filt)

    # 1. Calcular MARCA ZONAL SCORE para cada jugador vs su Position Group
    all_scores = {}

    # Porteros: usar pentágono GK (promedio simple de los 5 ejes)
    gk_df = df_filt[df_filt['Position Group'] == 'Portero']
    if not gk_df.empty:
        for _, row in gk_df.iterrows():
            gk_scores = _compute_pentagon_scores_gk(row, gk_df, all_cols)
            overall = float(np.mean(list(gk_scores.values()))) if gk_scores else 0.0
            all_scores[row['Player']] = {
                'name':     row['Player'],
                'puntaje':  round(overall, 1),
                'club':     str(row.get(team_col, '—')),
                'age':      (int(row['Age']) if 'Age' in row.index
                             and pd.notnull(row['Age']) else '—'),
                'position': str(row.get('Position', '')),
                'position_group': 'Portero',
            }

    # Outfield: usar pentágono + pesos por posición (_AXIS_WEIGHTS_BY_POS)
    for pos_group in ['Delantero', 'Extremo', 'Volante Central', 'Lateral', 'Central']:
        pos_df = df_filt[df_filt['Position Group'] == pos_group]
        if pos_df.empty:
            continue
        axis_w = _AXIS_WEIGHTS_BY_POS.get(pos_group, _DEFAULT_AXIS_WEIGHTS)
        total_w = sum(axis_w.values())
        for _, row in pos_df.iterrows():
            scores = _compute_pentagon_scores(row, pos_df, all_cols, position_group=pos_group)
            overall = sum(scores.get(k, 0) * v for k, v in axis_w.items()) / total_w if total_w else 0.0
            all_scores[row['Player']] = {
                'name':     row['Player'],
                'puntaje':  round(overall, 1),
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

    return {slot: _best_for_slot(slot) for slot in _B11_POS_MAP}, threshold


def _draw_best_eleven_fig(best_eleven, min_minutes, season_label=None, logo_path=None):
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
              f'{season_label or "2026"}  ·  Mínimo {min_minutes} min  ·  Ranking por percentil promedio',
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
    st.markdown(f"""
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
            Selección automática por posición · {_LIGA_TORNEO.get(liga_activa, '2026')} · Criterio: MARCA ZONAL SCORE
        </div>
    </div>
    """, unsafe_allow_html=True)

    b11_age_min, b11_age_max = _get_age_bounds(df)
    b11_age_range = st.slider(
        "Rango de edad", b11_age_min, b11_age_max,
        value=(b11_age_min, b11_age_max), key="b11_age_range"
    )
    b11_df = _apply_age_filter(df, b11_age_range)

    best_eleven, _b11_min_min = _compute_best_eleven(b11_df)

    # ── Figura (se genera una sola vez, se reutiliza para display y descarga) ──
    fig_b11     = _draw_best_eleven_fig(best_eleven, min_minutes=_b11_min_min,
                                        season_label=_LIGA_TORNEO.get(liga_activa, '2026'),
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
        f"Mínimo {_b11_min_min} min jugados (50% del máximo) · {b11_age_range[0]}-{b11_age_range[1]} años"
        f"  ·  X: @marca_zonal  ·  Instagram: @marca.zonal"
    )


# ---------------------------------------------------------------------------
# Tab: Buscador
# ---------------------------------------------------------------------------
with tab_query:

    # ── Session state ──────────────────────────────────────────────────────
    if 'bq_n' not in st.session_state:
        st.session_state['bq_n'] = 3

    st.subheader("Buscador avanzado")
    st.caption("Filtrá jugadores que cumplan múltiples umbrales de métricas simultáneamente")

    # ── Bloque 1: Posición y Club (cols reservadas, se rellenan más abajo) ──
    bq_c1, bq_c2 = st.columns(2)

    # ── Edad y Minutos ──────────────────────────────────────────────────────
    _bq_ref = df_all if not df_all.empty else df
    bq_age_min = int(pd.to_numeric(_bq_ref['Age'], errors='coerce').min()) if 'Age' in _bq_ref.columns else 15
    bq_age_max = int(pd.to_numeric(_bq_ref['Age'], errors='coerce').max()) if 'Age' in _bq_ref.columns else 45
    bq_min_v   = int(pd.to_numeric(_bq_ref['Minutes played'], errors='coerce').min()) if 'Minutes played' in _bq_ref.columns else 0
    bq_max_v   = int(pd.to_numeric(_bq_ref['Minutes played'], errors='coerce').max()) if 'Minutes played' in _bq_ref.columns else 5000

    bq_a1, bq_a2 = st.columns(2)
    with bq_a1:
        bq_age = st.slider("Rango de edad", bq_age_min, bq_age_max,
                           (bq_age_min, bq_age_max), key="bq_age")
    with bq_a2:
        bq_mins = st.slider("Minutos mínimos", bq_min_v, bq_max_v,
                            min(200, bq_max_v), key="bq_mins")

    # ── Ligas ───────────────────────────────────────────────────────────────
    _bq_liga_colors = {
        'PAR': '#dc2626', 'ARG': '#75caed', 'BRA': '#16a34a',
        'URU': '#2563eb', 'COL': '#eab308', 'ECU': '#7c3aed', 'CHI': '#f97316',
        'PER': '#e879f9', 'VEN': '#2dd4bf',
        'ING': '#e11d48', 'ITA': '#4ade80', 'ALE': '#f59e0b',
        'ESP': '#fb923c', 'FRA': '#60a5fa',
        'LIB':  '#10b981', 'SUD':  '#a78bfa',
        'UCL':  '#3b82f6', 'UEL':  '#fb923c', 'UECL': '#22d3ee',
    }
    _bq_liga_codes = [k for k in _AVAILABLE_LIGAS if _LIGA_DFS.get(k) is not None]

    _bq_ck_rules = '\n'.join(
        f'div[data-testid="stCheckbox"]:has(input[aria-label="{_LIGA_LABELS[c]}"]) label p'
        f' {{ color: {_bq_liga_colors.get(c, "#e2e8f0")} !important; }}'
        for c in _bq_liga_codes if c in _bq_liga_colors
    )
    st.markdown(f"""
    <style>
    div[data-testid="stCheckbox"]:has(input[aria-label="🌐 TODAS"]) label p
        {{ color: #22c55e !important; font-weight: 800 !important; }}
    div[data-testid="stCheckbox"] label p
        {{ font-weight: 800 !important; font-size: 0.9rem !important; }}
    {_bq_ck_rules}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        "<p style='margin:10px 0 5px 0; font-size:0.78rem; color:#9ca3af; font-weight:600;"
        " text-transform:uppercase; letter-spacing:0.06em;'>Ligas</p>",
        unsafe_allow_html=True,
    )
    _bq_todas_col, *_bq_ck_cols = st.columns([1] + [1] * len(_bq_liga_codes))
    with _bq_todas_col:
        bq_todas = st.checkbox("🌐 TODAS", value=True, key="bq_todas")

    bq_liga_sel = {}
    for _i, _code in enumerate(_bq_liga_codes):
        with _bq_ck_cols[_i]:
            bq_liga_sel[_code] = st.checkbox(
                _LIGA_LABELS[_code],
                value=True,
                disabled=bq_todas,
                key=f"bq_liga_{_code}",
            )

    selected_ligas_bq = _bq_liga_codes if bq_todas else [c for c, v in bq_liga_sel.items() if v]

    # ── Por 90 / Total ──────────────────────────────────────────────────────
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    bq_mode = st.radio("Métricas", ["Por 90", "Total"], horizontal=True,
                       key="bq_mode", label_visibility="collapsed")
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Pool completo (solo ligas seleccionadas) ────────────────────────────
    _bq_parts = []
    for _code in selected_ligas_bq:
        _ldf = _LIGA_DFS.get(_code)
        if _ldf is not None:
            _p = _ldf.copy()
            _p['Liga'] = _code
            _bq_parts.append(_p)
    bq_pool_full = pd.concat(_bq_parts, ignore_index=True) if _bq_parts else pd.DataFrame()

    # Posición multiselect (cascada: primero sobre pool completo)
    bq_pos_opts = sorted(bq_pool_full['Position Group'].dropna().unique()) if not bq_pool_full.empty else []
    with bq_c1:
        bq_pos = st.multiselect("Posición", bq_pos_opts, key="bq_pos",
                                placeholder="Todas las posiciones")

    bq_pool_pos = (bq_pool_full[bq_pool_full['Position Group'].isin(bq_pos)].copy()
                   if bq_pos else bq_pool_full.copy())

    # Club multiselect (cascada desde posición)
    _bq_tc = ('Team within selected timeframe'
              if not bq_pool_pos.empty and 'Team within selected timeframe' in bq_pool_pos.columns
              else 'Team')
    bq_clubs_avail = sorted(bq_pool_pos[_bq_tc].dropna().unique()) if not bq_pool_pos.empty else []
    with bq_c2:
        bq_club = st.multiselect("Club", bq_clubs_avail, key="bq_club",
                                 placeholder="Todos los clubes")

    # ── Pool base (pre-métricas) ────────────────────────────────────────────
    bq_pool = bq_pool_pos.copy()
    if bq_club:
        bq_pool = bq_pool[bq_pool[_bq_tc].isin(bq_club)]
    if 'Age' in bq_pool.columns:
        bq_pool = bq_pool[pd.to_numeric(bq_pool['Age'], errors='coerce').between(bq_age[0], bq_age[1])]
    if 'Minutes played' in bq_pool.columns:
        bq_pool = bq_pool[pd.to_numeric(bq_pool['Minutes played'], errors='coerce') >= bq_mins]
    bq_pool = bq_pool.reset_index(drop=True)

    # ── Métricas disponibles ────────────────────────────────────────────────
    if bq_mode == "Por 90":
        bq_avail = sorted([c for c in metric_columns
                           if (c.endswith(' per 90') or c.endswith(', %'))
                           and c in bq_pool.columns])
    else:
        bq_avail = sorted([c for c in metric_columns
                           if not c.endswith(' per 90')
                           and 'Average' not in c
                           and c in bq_pool.columns])

    # ── Selectores de métricas dinámicos ──────────────────────────────────
    st.markdown(
        "<p style='margin:14px 0 5px 0; font-size:0.78rem; color:#9ca3af; font-weight:600;"
        " text-transform:uppercase; letter-spacing:0.06em;'>Métricas y umbrales</p>",
        unsafe_allow_html=True,
    )

    bq_active_filters = []  # list of (col_name, min_val, max_val)

    for _i in range(st.session_state['bq_n']):
        _mc1, _mc2 = st.columns([1, 2])
        with _mc1:
            _sel = st.selectbox(
                f"Métrica {_i + 1}",
                ['—'] + bq_avail,
                key=f"bq_metric_{_i}",
                format_func=lambda x: '—' if x == '—' else translate(x),
            )
        if _sel != '—' and not bq_pool.empty and _sel in bq_pool.columns:
            _series = pd.to_numeric(bq_pool[_sel], errors='coerce').dropna()
            if len(_series) >= 2:
                _s_min = float(round(_series.min(), 2))
                _s_max = float(round(_series.max(), 2))
                if _s_min == _s_max:
                    _s_max = _s_min + 0.01
                _step = max(round((_s_max - _s_min) / 200, 3), 0.01)
                with _mc2:
                    _rng = st.slider(
                        translate(_sel),
                        min_value=_s_min, max_value=_s_max,
                        value=(_s_min, _s_max),
                        step=_step,
                        key=f"bq_rng_{_i}_{_sel}",
                    )
                bq_active_filters.append((_sel, _rng[0], _rng[1]))
        else:
            with _mc2:
                st.markdown("<div style='height:38px'></div>", unsafe_allow_html=True)

    # Botones agregar / quitar
    _bq_b1, _bq_b2, _ = st.columns([1, 1, 5])
    with _bq_b1:
        if st.session_state['bq_n'] < 7:
            if st.button("＋ Agregar métrica", key="bq_add", use_container_width=True):
                st.session_state['bq_n'] += 1
                st.rerun()
    with _bq_b2:
        if st.session_state['bq_n'] > 1:
            if st.button("－ Quitar", key="bq_remove", use_container_width=True):
                st.session_state['bq_n'] -= 1
                st.rerun()

    # ── Aplicar filtros de métricas ─────────────────────────────────────────
    bq_result = bq_pool.copy()
    for _col, _mn, _mx in bq_active_filters:
        if _col in bq_result.columns:
            _n = pd.to_numeric(bq_result[_col], errors='coerce')
            bq_result = bq_result[(_n >= _mn) & (_n <= _mx)]
    bq_result = bq_result.reset_index(drop=True)
    n_bq = len(bq_result)

    # ── Controles de orden ──────────────────────────────────────────────────
    _bq_sort_opts = ['Jugador', 'Edad', 'Minutos'] + [translate(f[0]) for f in bq_active_filters]
    _bq_sort_map  = {'Jugador': 'Player', 'Edad': 'Age', 'Minutos': 'Minutes played'}
    for _col, _, _ in bq_active_filters:
        _bq_sort_map[translate(_col)] = _col

    _bs1, _bs2 = st.columns([2, 1])
    with _bs1:
        bq_sort_lbl = st.selectbox("Ordenar por", _bq_sort_opts, key="bq_sort")
    with _bs2:
        bq_sort_dir = st.radio("Orden", ["↓ Mayor a menor", "↑ Menor a mayor"],
                               key="bq_ord", horizontal=True, label_visibility="collapsed")

    bq_sort_col = _bq_sort_map.get(bq_sort_lbl, 'Player')
    bq_asc      = (bq_sort_dir == "↑ Menor a mayor")

    if not bq_result.empty and bq_sort_col in bq_result.columns:
        try:
            bq_result = bq_result.sort_values(
                bq_sort_col, ascending=bq_asc,
                key=lambda s: pd.to_numeric(s, errors='coerce') if bq_sort_col != 'Player' else s
            ).reset_index(drop=True)
        except Exception:
            pass

    # ── Contador de resultados ─────────────────────────────────────────────
    st.markdown(
        f"<p style='margin:12px 0 6px 0; font-size:0.9rem; color:#94a3b8;'>"
        f"<b style='color:#22c55e; font-size:1rem;'>{n_bq}</b> "
        f"jugador{'es' if n_bq != 1 else ''} encontrado{'s' if n_bq != 1 else ''}"
        f"</p>",
        unsafe_allow_html=True,
    )

    # ── HTML Table ──────────────────────────────────────────────────────────
    if not bq_result.empty and n_bq > 0 and bq_active_filters:
        _bq_tc_r = ('Team within selected timeframe'
                    if 'Team within selected timeframe' in bq_result.columns else 'Team')
        _show_liga = ('Liga' in bq_result.columns and len(selected_ligas_bq) > 1)
        _bq_badge = {
            'PAR': '#dc2626', 'ARG': '#75caed', 'BRA': '#16a34a',
            'URU': '#2563eb', 'COL': '#eab308', 'ECU': '#7c3aed', 'CHI': '#f97316',
            'PER': '#e879f9', 'VEN': '#2dd4bf',
            'ING': '#ef4444', 'ITA': '#84cc16', 'ALE': '#facc15',
            'ESP': '#f97316', 'FRA': '#60a5fa',
            'LIB': '#10b981', 'SUD': '#a78bfa',
            'UCL': '#3b82f6', 'UEL': '#fb923c', 'UECL': '#22d3ee',
        }

        # Cabeceras métricas con rango del slider
        def _fmt_threshold(mn, mx, col):
            _all = pd.to_numeric(bq_pool[col], errors='coerce') if col in bq_pool.columns else pd.Series(dtype=float)
            _pool_min = float(_all.min()) if len(_all) > 0 else mn
            _pool_max = float(_all.max()) if len(_all) > 0 else mx
            at_min = abs(mn - _pool_min) < 0.011
            at_max = abs(mx - _pool_max) < 0.011
            if at_min and at_max:
                return ''
            if at_min:
                return f'≤ {mx:.2f}'
            if at_max:
                return f'≥ {mn:.2f}'
            return f'{mn:.2f} – {mx:.2f}'

        # Header row
        _th_metric = ''.join(
            f'<th class="mth">{translate(col)}'
            f'{"<br><span class=thr>" + _fmt_threshold(mn, mx, col) + "</span>" if _fmt_threshold(mn, mx, col) else ""}'
            f'</th>'
            for col, mn, mx in bq_active_filters
        )
        _liga_th = '<th>Liga</th>' if _show_liga else ''

        # Data rows
        _rows = ''
        for _, row in bq_result.iterrows():
            _player = str(row.get('Player', ''))
            _age    = str(int(row['Age'])) if pd.notna(row.get('Age')) and str(row.get('Age')) != 'nan' else '—'
            _nat    = str(row.get('Birth country', '—')).strip() or '—'
            _club   = str(row.get(_bq_tc_r, '—'))

            _rows += '<tr>'
            _rows += f'<td class="pname">{_player}</td>'
            _rows += f'<td class="ctr">{_age}</td>'
            _rows += f'<td class="nat">{_nat}</td>'
            _rows += f'<td>{_club}</td>'

            if _show_liga:
                _lc = str(row.get('Liga', ''))
                _bc = _bq_badge.get(_lc, '#64748b')
                _rows += (f'<td><span style="background:{_bc};color:#fff;padding:2px 7px;'
                          f'border-radius:4px;font-size:10px;font-weight:700;">{_lc}</span></td>')

            for _col, _mn, _mx in bq_active_filters:
                _v = pd.to_numeric(row.get(_col), errors='coerce')
                if pd.isna(_v):
                    _rows += '<td class="ctr">—</td>'
                else:
                    _vs = f'{_v:.2f}' if bq_mode == "Por 90" else (f'{int(_v)}' if _v == int(_v) else f'{_v:.2f}')
                    _rows += f'<td class="mval">{_vs}</td>'

            _rows += '</tr>'

        _table_h = min(580, 46 + n_bq * 40 + 20)

        _html = f"""<!DOCTYPE html><html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Cousine:wght@400;700&family=Poppins:wght@600;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0f172a;color:#e2e8f0;font-family:'Cousine',monospace;font-size:13px}}
.wrap{{overflow-x:auto;overflow-y:auto;max-height:{_table_h}px}}
table{{width:100%;border-collapse:collapse;min-width:500px}}
thead tr{{background:#1e293b;position:sticky;top:0;z-index:1}}
th{{padding:10px 14px;text-align:left;color:#94a3b8;font-size:10.5px;
    font-family:'Poppins',sans-serif;text-transform:uppercase;letter-spacing:0.07em;
    font-weight:700;border-bottom:2px solid #334155;white-space:nowrap}}
th.mth{{color:#f59e0b}}
.thr{{color:#64748b;font-size:9px;font-weight:400;text-transform:none;letter-spacing:0}}
td{{padding:8px 14px;border-bottom:1px solid #1e293b;white-space:nowrap}}
tr:hover td{{background:rgba(255,255,255,0.03)}}
.pname{{color:#f1f5f9;font-weight:700}}
.mval{{color:#22c55e;font-weight:700}}
.ctr{{text-align:center}}
.nat{{color:#94a3b8;font-size:12px}}
</style>
</head>
<body>
<div class="wrap">
<table>
<thead><tr>
<th>Jugador</th><th class="ctr">Edad</th><th>Nac.</th><th>Club</th>
{_liga_th}{_th_metric}
</tr></thead>
<tbody>{_rows}</tbody>
</table>
</div>
</body></html>"""

        components.html(_html, height=_table_h + 30, scrolling=False)

    elif bq_active_filters and n_bq == 0:
        st.info("Ningún jugador cumple todos los criterios. Probá ampliar los rangos.")
    elif not bq_active_filters:
        st.info("Seleccioná al menos una métrica para ver resultados.")


# ---------------------------------------------------------------------------
# Footer — contador de visitas
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(f"👁️ Visitas a la app: **{_visit_count:,}**  ·  Marca Zonal · {_LIGA_TORNEO.get(liga_activa, '2026')}")
