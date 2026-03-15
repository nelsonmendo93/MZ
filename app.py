import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import io
import os
import matplotlib
matplotlib.use('Agg')
from collections import defaultdict

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
        'Defensive duels per 90',
        'Defensive duels won, %',
        'Aerial duels per 90',
        'Interceptions per 90',
        'Sliding tackles per 90',
    ],
    'Ataque': [
        'Goals per 90',
        'Shots per 90',
        'Assists per 90',
        'Dribbles per 90',
        'Touches in box per 90',
    ],
    'Distribución': [
        'Accurate passes, %',
        'Shot assists per 90',
        'Passes to final third per 90',
        'Progressive passes per 90',
        'Key passes per 90',
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
st.set_page_config(page_title="Portal de Datos", layout="wide")

# Professional theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Poppins:wght@600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Roboto', sans-serif;
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

if os.path.exists(LOGO_BLANCO):
    st.image(LOGO_BLANCO, width=1000)
st.caption("Bienvenidos al portal de datos de Marca Zonal · Datos actualizados semanalmente")

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
        return '\u26a1 Ataque'
    if 'received' in cl:
        return '\U0001f4e5 Recepci\u00f3n'
    if 'assist' in cl or cl.startswith('xa'):
        return '\U0001f3af Creaci\u00f3n'
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
        return '\u26a1 Ataque'
    if any(k in cl for k in ['foul', 'card', 'yellow', 'red']):
        return '\U0001f4cb Disciplina'
    if any(k in cl for k in ['corner', 'free kick']):
        return '\U0001f945 Pelota Parada'
    return '\U0001f4ca Otros'

CATEGORY_ORDER = [
    '\u26bd Goles y Remates', '\U0001f3af Creaci\u00f3n', '\U0001f4d0 Pases',
    '\u2197\ufe0f Centros', '\u26a1 Ataque', '\U0001f4aa Duelos',
    '\U0001f6e1\ufe0f Defensa', '\U0001f4e5 Recepci\u00f3n',
    '\U0001f4cb Disciplina', '\U0001f945 Pelota Parada', '\U0001f4ca Otros',
]

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_table, tab_xy, tab_bar, tab_pizza = st.tabs(
    ["📊 Tabla de datos", "📈 Gráfico XY", "📊 Barras - Percentiles", "🎯 Radial"]
)

# ---- Tab 1: Data Table ---------------------------------------------------

# Color map per metric category
CATEGORY_COLORS = {
    '\U0001f6e1\ufe0f Defensa':      '#eab308',   # amarillo
    '\U0001f4aa Duelos':             '#eab308',   # amarillo
    '\u26a1 Ataque':                 '#ef4444',   # rojo
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
        font-family: 'Roboto', Arial, sans-serif;
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
        font-family: 'Poppins', 'Roboto', sans-serif;
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

        # Collect per-90 + percentage metrics only (most comparable)
        show_cols = [
            c for c in df.columns
            if (c.endswith(' per 90') or c.endswith(', %'))
            and c not in NON_METRIC_COLS
            and c not in HIDDEN_TABLE_COLS
            and pd.api.types.is_numeric_dtype(df[c])
        ]

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
                                     y_label=translate(y_metric))
            st.pyplot(fig_xy)

            # Download button
            buf = io.BytesIO()
            fig_xy.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                           facecolor=fig_xy.get_facecolor())
            st.download_button("⬇️ Descargar grafica", buf.getvalue(),
                               file_name="grafico_xy_marcazonal.png", mime="image/png")

# ---- Tab 3: Bar Chart Comparison ------------------------------------------
with tab_bar:
    st.subheader("Grafico de Barras por percentiles")

    # Club → Player selection (inside the tab)
    team_col = 'Team within selected timeframe'
    if team_col not in df.columns:
        team_col = 'Team'
    all_clubs = sorted(df[team_col].dropna().unique())

    bar_col1, bar_col2 = st.columns(2)
    with bar_col1:
        bar_club = st.selectbox("Club", all_clubs, key="bar_club")
    club_players = sorted(df[df[team_col] == bar_club]['Player'].dropna().unique())
    with bar_col2:
        bar_player = st.selectbox("Jugador", club_players, key="bar_player")

    # Minutes slider
    bar_min_min = int(df['Minutes played'].min()) if 'Minutes played' in df.columns else 0
    bar_max_min = int(df['Minutes played'].max()) if 'Minutes played' in df.columns else 100
    bar_min_minutes = st.slider(
        "Minutos mínimos jugados", bar_min_min, bar_max_min,
        value=min(200, bar_max_min), key="bar_min_minutes"
    )

    # Find the player's position group
    player_rows = df[df['Player'] == bar_player]
    if player_rows.empty:
        st.warning("Jugador no encontrado.")
    else:
        player_data = player_rows.iloc[0]
        pos_group = player_data.get('Position Group', None)

        if pd.isna(pos_group):
            st.warning("El jugador no tiene grupo de posición asignado.")
        else:
            # Filter comparison group: same position group + min minutes
            bar_group_df = df[
                (df['Position Group'] == pos_group)
                & (df['Minutes played'] >= bar_min_minutes)
            ].copy()

            # Check that the player is in the filtered group
            player_in_group = bar_group_df[bar_group_df['Player'] == bar_player]
            if player_in_group.empty:
                st.warning("El jugador no cumple el filtro de minutos mínimos. Reducí el slider.")
            else:
                player_data = player_in_group.iloc[0]
                n_players = len(bar_group_df)

                # Build categories_data for the chart
                categories_data = []
                for cat_name, metric_list in BAR_METRICS.items():
                    cat_metrics = []
                    for m in metric_list:
                        if m not in bar_group_df.columns:
                            continue
                        col = pd.to_numeric(bar_group_df[m], errors='coerce')
                        val = pd.to_numeric(player_data[m], errors='coerce')
                        mn = float(col.min()) if pd.notnull(col.min()) else 0
                        mx = float(col.max()) if pd.notnull(col.max()) else 1
                        if mn == mx:
                            mx = mn + 1
                        v = float(val) if pd.notnull(val) else 0
                        pct = max(0, min(100, (v - mn) / (mx - mn) * 100))
                        cat_metrics.append((translate(m), round(pct, 1)))
                    if cat_metrics:
                        categories_data.append((cat_name, cat_metrics))

                if not categories_data:
                    st.warning("No hay métricas disponibles para generar el gráfico.")
                else:
                    team_display = str(player_data.get(team_col, ''))
                    subtitle = f"Entre {n_players} {pos_group.lower()}s +{bar_min_minutes} min | Apertura 2026"

                    fig_bar = create_bar_chart(
                        player_name=bar_player,
                        player_team=team_display,
                        subtitle=subtitle,
                        categories_data=categories_data,
                    )
                    st.pyplot(fig_bar)

                    buf2 = io.BytesIO()
                    fig_bar.savefig(buf2, format='png', dpi=200, bbox_inches='tight',
                                    facecolor=fig_bar.get_facecolor())
                    st.download_button("⬇️ Descargar grafica", buf2.getvalue(),
                                       file_name="comparativa_marcazonal.png", mime="image/png",
                                       key="dl_bar")

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
