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
import matplotlib.font_manager as _fm
from collections import defaultdict
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from utils.data_processing import load_and_process_data
from utils.xy_chart import create_xy_chart
from utils.bar_chart import create_bar_chart
from utils.pizza_chart import create_pizza_chart
from utils.translations import translate

# Logo paths
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
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
}

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Contador de visitas — persiste en data/visit_counter.json
# Se incrementa una sola vez por sesión (no en cada rerun de Streamlit)
# ---------------------------------------------------------------------------
_COUNTER_FILE = os.path.join(_APP_DIR, 'data', 'visit_counter.json')


def _load_visits():
    """Lee el total de visitas desde el archivo JSON."""
    if os.path.exists(_COUNTER_FILE):
        with open(_COUNTER_FILE, 'r') as f:
            return json.load(f).get('visits', 0)
    return 0


def _increment_visits():
    """Incrementa el contador y lo guarda. Retorna el nuevo total."""
    count = _load_visits() + 1
    with open(_COUNTER_FILE, 'w') as f:
        json.dump({'visits': count}, f)
    return count


# Contar solo en sesiones nuevas (la primera vez que el usuario carga la página)
if 'visit_counted' not in st.session_state:
    st.session_state['visit_counted'] = True
    _visit_count = _increment_visits()
else:
    _visit_count = _load_visits()


st.set_page_config(page_title="Portal de Datos", layout="wide")

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
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(6, 182, 212, 0.04));
    border: 1px solid rgba(14, 165, 233, 0.2);
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
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


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
    """Group a metric into a display category."""
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
    if any(k in cl for k in ['goal', 'shot', 'xg', 'penalty', 'conversion']):
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

CATEGORY_ORDER = [
    '\u26bd Goles y Remates', '\U0001f3af Creaci\u00f3n', '\U0001f4d0 Pases',
    '\u2197\ufe0f Centros', '\u26a1 Posesi\u00f3n', '\U0001f4aa Duelos',
    '\U0001f6e1\ufe0f Defensa', '\U0001f4e5 Recepci\u00f3n',
    '\U0001f4cb Disciplina', '\U0001f4ca Otros',
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


def _get_display_cols(df):
    """Devuelve las columnas curadas para barras de percentiles y pentágono OVERALL.
    Solo métricas de calidad: %, Accurate, won y categorías completas."""
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
# Tabs
# ---------------------------------------------------------------------------
tab_table, tab_xy, tab_bar, tab_pizza, tab_similar = st.tabs(
    ["📊 Tabla de datos", "📈 Gráfico XY", "🏆 OVERALL", "🎯 Radial", "🔍 Similares"]
)

# ---- Tab 1: Data Table ---------------------------------------------------

# Color map per metric category
CATEGORY_COLORS = {
    '\U0001f6e1\ufe0f Defensa':      '#eab308',   # amarillo
    '\U0001f4aa Duelos':             '#eab308',   # amarillo
    '\u26a1 Posesi\u00f3n':                 '#ef4444',   # rojo
    '\u26bd Goles y Remates':        '#ef4444',   # rojo
    '\U0001f3af Creaci\u00f3n':      '#f97316',   # naranja
    '\u2197\ufe0f Centros':          '#8b5cf6',   # violeta
    '\U0001f4d0 Pases':              '#3b82f6',   # azul
    '\U0001f4e5 Recepci\u00f3n':     '#14b8a6',   # teal
    '\U0001f4cb Disciplina':         '#6b7280',   # gris
    '\U0001f945 Pelota Parada':      '#10b981',   # verde
    '\U0001f4ca Otros':              '#94a3b8',   # slate
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


def _create_pentagon_chart(scores, player_name, team, subtitle, avg_scores=None,
                           pos_label='', scores2=None, player2_name=''):
    """Dibuja el gráfico pentágono estilo Sofascore con matplotlib.
    Si scores2 se provee, dibuja dos polígonos (verde P1, azul P2) y badges apilados."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    labels     = ['ATQ', 'POS', 'PAS', 'DEF', 'CRE']
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
                               facecolor='#0ea5e925', edgecolor='#38bdf8', linewidth=2.5,
                               zorder=4)
        ax.add_patch(pl2_poly)

    # Polígono jugador 1 (verde, encima)
    pl_poly = plt.Polygon(list(zip(pl_x, pl_y)), closed=True,
                          facecolor='#16a34a25', edgecolor='#22c55e', linewidth=2.5,
                          zorder=5)
    ax.add_patch(pl_poly)

    # Punto central
    ax.plot(0, 0, 'o', color='#22c55e', markersize=5, zorder=7)
    if compare_mode:
        ax.plot(0, 0, 'o', color='#38bdf8', markersize=3, zorder=8)

    # Badges en vértices
    offset = 1.36
    for label, angle, score in zip(labels, angles, score_vals):
        bx = offset * np.cos(angle)
        by = offset * np.sin(angle)
        avg_val = avg_scores.get(label, 50) if avg_scores else 50

        if compare_mode:
            sc2 = scores2.get(label, 0)
            # Badge P1 siempre verde (color de referencia)
            ax.text(bx, by + 0.20, str(score), ha='center', va='center',
                    fontsize=13, fontweight='bold', color='#fff',
                    bbox=dict(boxstyle='round,pad=0.26', facecolor='#166534', edgecolor='none'),
                    zorder=9)
            # Badge P2 siempre azul (color de referencia)
            ax.text(bx, by - 0.02, str(sc2), ha='center', va='center',
                    fontsize=13, fontweight='bold', color='#fff',
                    bbox=dict(boxstyle='round,pad=0.26', facecolor='#0369a1', edgecolor='none'),
                    zorder=9)
            ax.text(bx, by - 0.26, label, ha='center', va='center',
                    fontsize=10, fontweight='bold', color='#9ca3af', zorder=9)
        else:
            # Badge único (modo individual)
            if score >= 70 and score > avg_val:
                badge_col, txt_col = '#ca8a04', '#fff'
            elif score >= avg_val:
                badge_col, txt_col = '#166534', '#fff'
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

    # Leyenda
    if compare_mode:
        legend_items = [
            mpatches.Patch(color='#22c55e', label=f'■ {player_name[:18]}'),
            mpatches.Patch(color='#38bdf8', label=f'■ {player2_name[:18]}'),
            mpatches.Patch(facecolor='none', edgecolor='#94a3b8',
                           linestyle='--', label=f'Prom. {pos_label}'),
            mpatches.Patch(color='#ca8a04', label='Dest. P1 (≥70 y sobre prom.)'),
        ]
    else:
        legend_items = [
            mpatches.Patch(color='#22c55e', label='Jugador'),
            mpatches.Patch(facecolor='none', edgecolor='#94a3b8',
                           linestyle='--', label=f'Promedio {pos_label}'),
            mpatches.Patch(color='#ca8a04', label='Destacado (≥70 y sobre prom.)'),
            mpatches.Patch(color='#166534', label='Sobre el promedio'),
            mpatches.Patch(color='#374151', label='Bajo el promedio'),
        ]
    ax.legend(handles=legend_items, loc='lower center', ncol=2,
              facecolor='#0f1117', edgecolor='#2d3748',
              labelcolor='#9ca3af', fontsize=7.8,
              bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout(pad=0.3)

    # Watermark — logo encima de la leyenda con opacidad 20%
    import matplotlib.image as mpimg
    if os.path.exists(LOGO_BLANCO):
        try:
            logo = mpimg.imread(LOGO_BLANCO)
            # Posición: centrado horizontalmente, 20% más arriba de la leyenda
            logo_ax = fig.add_axes([0.115, 0.19, 0.77, 0.084])
            logo_ax.imshow(logo, alpha=0.14)
            logo_ax.axis('off')
            logo_ax.patch.set_alpha(0)   # fondo transparente
        except Exception:
            fig.text(0.5, 0.06, '@marca_zonal', size=8, color='#ffffff',
                     ha='center', alpha=0.2, fontstyle='italic')

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

    # Min-minutes slider for the comparison pool
    t1_min_v = int(df['Minutes played'].min()) if 'Minutes played' in df.columns else 0
    t1_max_v = int(df['Minutes played'].max()) if 'Minutes played' in df.columns else 100
    tab1_min_minutes = st.slider(
        "Minutos mínimos (para percentiles)", t1_min_v, t1_max_v,
        value=min(200, t1_max_v), key="tab1_min_minutes"
    )

    # Display selected player data
    player_rows = club_pos_df[club_pos_df['Player'] == selected_player_tab1]
    if not player_rows.empty:
        player_data = player_rows.iloc[0]

        # Player header
        st.subheader(selected_player_tab1)
        pos_display = player_data.get('Position', '')
        st.caption(f"\U0001f4cd {pos_display}  ·  {selected_pos}")

        # Basic info cards
        ic1, ic2, ic3, ic4 = st.columns(4)
        ic1.metric("Equipo", str(player_data.get(team_col_tab1, '')))
        age_val = player_data.get('Age', None)
        ic2.metric("Edad", int(age_val) if pd.notnull(age_val) else '\u2014')
        mp_val = player_data.get('Matches played', None)
        ic3.metric("PJ", int(mp_val) if pd.notnull(mp_val) else '\u2014')
        mins_val = player_data.get('Minutes played', None)
        ic4.metric("Minutos", int(mins_val) if pd.notnull(mins_val) else '\u2014')

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

        # Métricas curadas — usa la misma función compartida con el pentágono OVERALL
        show_cols = _get_display_cols(df)

        # Group and compute percentiles
        categorized = defaultdict(list)
        for c in show_cols:
            val = player_data.get(c, None)
            if pd.isnull(val):
                continue
            player_val = float(val)
            pct = _compute_percentile(player_val, comparison_df[c]) if c in comparison_df.columns else 0
            formatted = f"{player_val:.2f}"
            cat = categorize_metric(c)
            categorized[cat].append({
                'metric': translate(c),
                'value':  formatted,
                'pct':    pct,
            })

        # Render bars — all categories in one component call
        if categorized:
            _render_all_bars(categorized, CATEGORY_ORDER, CATEGORY_COLORS)
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

    # Only per-90 metrics
    per90_columns = sorted([c for c in metric_columns if c.endswith(' per 90')])
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
    pent_pos_groups = sorted(df['Position Group'].dropna().unique())
    with pent_col1:
        pent_pos = st.selectbox("Posición", pent_pos_groups, key="pent_pos")
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
            # Métricas curadas — las mismas que Tab 1 (calidad, no volumen)
            all_pent_cols = _get_display_cols(df)

            scores = _compute_pentagon_scores(
                pent_player_data, pent_comparison_df, all_pent_cols
            )
            avg_scores = _compute_avg_pentagon_scores(pent_comparison_df, all_pent_cols)

            # Calcular scores del jugador 2 si el comparador está activo
            scores2 = None
            if st.session_state['pent_show_compare'] and pent_player2:
                p2_rows = pent_pos_df[pent_pos_df['Player'] == pent_player2]
                if not p2_rows.empty:
                    p2_data = p2_rows.iloc[0]
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

            # Tabla resumen de puntajes debajo del gráfico
            st.markdown("#### Detalle de puntajes")
            group_desc = {
                'ATQ': 'Goles y Remates',
                'POS': 'Posesión (Dribbling, Recepción, Acciones ofensivas)',
                'PAS': 'Pases y Centros',
                'CRE': 'Creatividad',
                'DEF': 'Defensa y Duelos (con penalización por Disciplina)',
            }
            summary_rows = []
            for key in ['ATQ', 'POS', 'PAS', 'CRE', 'DEF']:
                diff = scores[key] - avg_scores[key]
                row = {
                    'Categoría': key,
                    'Descripción': group_desc[key],
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

            st.markdown(f"""
            <div style="background:#1a1f2e; border:1px solid #2d3748; border-radius:12px;
                        padding:16px 24px; margin-bottom:16px; display:flex; align-items:center; gap:20px;">
              <div>
                <div style="font-size:1.4rem; font-weight:800; color:#f1f5f9;">{sim_player}</div>
                <div style="color:#9ca3af; font-size:0.9rem; margin-top:4px;">
                  {sim_player_team} &nbsp;·&nbsp; {sim_pos} &nbsp;·&nbsp; {sim_player_mins:,} mins
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

# ---------------------------------------------------------------------------
# Footer — contador de visitas
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(f"👁️ Visitas a la app: **{_visit_count:,}**  ·  Marca Zonal · Apertura 2026")
