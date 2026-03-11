import streamlit as st
import pandas as pd
import io
import os
import matplotlib
matplotlib.use('Agg')
from collections import defaultdict

from utils.data_processing import load_and_process_data
from utils.xy_chart import create_xy_chart
from utils.bar_chart import create_bar_chart
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
tab_table, tab_xy, tab_bar = st.tabs(
    ["📊 Tabla de datos", "📈 Gráfico XY", "📊 Barras - Percentiles"]
)

# ---- Tab 1: Data Table ---------------------------------------------------
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

    # Toggle per-90 / totals
    data_view = st.radio(
        "Tipo de datos", ["Totales", "Por 90"], horizontal=True, key="data_view"
    )

    # Display selected player data
    player_rows = club_pos_df[club_pos_df['Player'] == selected_player_tab1]
    if not player_rows.empty:
        player_data = player_rows.iloc[0]

        # Player header with position
        st.subheader(selected_player_tab1)
        pos_display = player_data.get('Position', '')
        st.caption(f"\U0001f4cd {pos_display} · {selected_pos}")

        # Basic info as metric cards
        ic1, ic2, ic3, ic4 = st.columns(4)
        ic1.metric("Equipo", str(player_data.get(team_col_tab1, '')))
        age_val = player_data.get('Age', None)
        ic2.metric("Edad", int(age_val) if pd.notnull(age_val) else '\u2014')
        mp_val = player_data.get('Matches played', None)
        ic3.metric("PJ", int(mp_val) if pd.notnull(mp_val) else '\u2014')
        mins_val = player_data.get('Minutes played', None)
        ic4.metric("Minutos", int(mins_val) if pd.notnull(mins_val) else '\u2014')

        st.markdown("---")

        # Select metrics based on data view (exclude info already shown)
        info_shown = {'Age', 'Matches played', 'Minutes played'}
        if data_view == "Por 90":
            show_cols = sorted([
                c for c in df.columns
                if c.endswith(' per 90')
                and c not in NON_METRIC_COLS and c not in HIDDEN_TABLE_COLS
                and c not in info_shown
                and pd.api.types.is_numeric_dtype(df[c])
            ])
        else:
            show_cols = sorted([
                c for c in df.columns
                if c not in NON_METRIC_COLS and c not in HIDDEN_TABLE_COLS
                and c not in info_shown
                and not c.endswith(' per 90')
                and pd.api.types.is_numeric_dtype(df[c])
            ])

        # Group metrics by category
        categorized = defaultdict(list)
        for c in show_cols:
            val = player_data.get(c, None)
            if pd.notnull(val):
                cat = categorize_metric(c)
                if c.endswith(' per 90') or ', %' in c:
                    formatted = f"{float(val):.2f}"
                else:
                    formatted = f"{float(val):.0f}"
                categorized[cat].append({'M\u00e9trica': translate(c), 'Valor': formatted})

        # Display categories in order with expanders
        if categorized:
            for cat in CATEGORY_ORDER:
                if cat in categorized:
                    with st.expander(cat, expanded=True):
                        st.dataframe(
                            pd.DataFrame(categorized[cat]),
                            use_container_width=True,
                            hide_index=True,
                        )
        else:
            st.info("No hay m\u00e9tricas disponibles para mostrar.")
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
