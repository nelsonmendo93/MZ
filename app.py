import streamlit as st
import pandas as pd
import io
import matplotlib
matplotlib.use('Agg')

from utils.data_processing import load_and_process_data
from utils.xy_chart import create_xy_chart
from utils.pizza_chart import create_pizza_chart
from utils.translations import translate

# ---------------------------------------------------------------------------
# Radar metrics — same 15 metrics for all position groups
# (5 defense + 5 attack + 5 distribution)
# ---------------------------------------------------------------------------
RADAR_METRICS = {
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
st.set_page_config(page_title="Marca Zonal - Portal de Datos", layout="wide")
st.title("⚽ Bienvenidos al portal de datos de Marca Zonal")
st.caption("Datos actualizados semanalmente")

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
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("Filtros")

position_groups = sorted(df['Position Group'].dropna().unique())
selected_group = st.sidebar.selectbox("Grupo de posición", position_groups)

# Filter players by position group
group_df = df[df['Position Group'] == selected_group].copy()

players_in_group = sorted(group_df['Player'].dropna().unique())
selected_player = st.sidebar.selectbox("Jugador", players_in_group)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros de tabla")

# 3 metric filters with range sliders
selected_metrics = []
metric_ranges = []
for i in range(1, 4):
    metric = st.sidebar.selectbox(
        f"Métrica {i}", [None] + metric_columns, key=f"metric_{i}",
        format_func=lambda x: translate(x) if x else "—"
    )
    if metric and metric in group_df.columns:
        col_data = pd.to_numeric(group_df[metric], errors='coerce').dropna()
        if not col_data.empty:
            min_val = float(col_data.min())
            max_val = float(col_data.max())
            rng = st.sidebar.slider(
                f"Rango {translate(metric)}", min_val, max_val, (min_val, max_val),
                key=f"range_{i}"
            )
            selected_metrics.append(metric)
            metric_ranges.append(rng)

limit = st.sidebar.number_input("Jugadores a mostrar", min_value=1,
                                 max_value=500, value=25)

# ---------------------------------------------------------------------------
# Apply metric filters to group_df for the table
# ---------------------------------------------------------------------------
filtered_df = group_df.copy()
for metric, rng in zip(selected_metrics, metric_ranges):
    col = pd.to_numeric(filtered_df[metric], errors='coerce')
    filtered_df = filtered_df[(col >= rng[0]) & (col <= rng[1])]

# Sort by selected metrics descending (if any), then limit
if selected_metrics:
    filtered_df = filtered_df.sort_values(
        by=selected_metrics, ascending=[False] * len(selected_metrics)
    )
filtered_df = filtered_df.head(limit)

# Choose visible columns
base_cols = ['Player', 'Team', 'Age', 'Matches played', 'Minutes played']

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_table, tab_xy, tab_radar = st.tabs(
    ["📊 Tabla de datos", "📈 Gráfico XY", "🍕 Radar"]
)

# ---- Tab 1: Data Table ---------------------------------------------------
with tab_table:
    st.subheader(f"Jugadores — {selected_group}")

    # Toggle per-90 / totals
    data_view = st.radio(
        "Tipo de datos", ["Totales", "Por 90"], horizontal=True, key="data_view"
    )

    if selected_metrics:
        visible_cols = [c for c in base_cols if c in filtered_df.columns] + selected_metrics
    elif data_view == "Por 90":
        per90_table = [c for c in filtered_df.columns
                       if c.endswith(' per 90') and c not in HIDDEN_TABLE_COLS]
        visible_cols = [c for c in base_cols if c in filtered_df.columns] + sorted(per90_table)
    else:
        visible_cols = [c for c in filtered_df.columns
                        if c not in HIDDEN_TABLE_COLS and not c.endswith(' per 90')]

    # Highlight selected player
    translated_col_map = {c: translate(c) for c in visible_cols}
    display_df = filtered_df[visible_cols].rename(columns=translated_col_map).reset_index(drop=True)

    # Decimal formatting: 2 for per-90 & %, 0 for totals
    fmt = {}
    for orig, es in translated_col_map.items():
        if not pd.api.types.is_numeric_dtype(filtered_df[orig]):
            continue
        if orig.endswith(' per 90') or ', %' in orig:
            fmt[es] = '{:.2f}'
        else:
            fmt[es] = '{:.0f}'

    player_col_es = translate('Player')
    def highlight_player(row):
        if row[player_col_es] == selected_player:
            return ['background-color: #2a6f97; color: white'] * len(row)
        return [''] * len(row)

    styled = display_df.style.apply(highlight_player, axis=1).format(fmt, na_rep='')
    st.dataframe(styled, use_container_width=True, height=600)

# ---- Tab 2: XY Chart -----------------------------------------------------
with tab_xy:
    st.subheader("Gráfico XY comparativo")

    # Only per-90 metrics
    per90_columns = sorted([c for c in metric_columns if c.endswith(' per 90')])
    if not per90_columns:
        st.warning("No se encontraron métricas 'por 90' en los datos.")
    else:
        # Minutes slider
        min_min = int(group_df['Minutes played'].min()) if 'Minutes played' in group_df.columns else 0
        max_min = int(group_df['Minutes played'].max()) if 'Minutes played' in group_df.columns else 100
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
        xy_df = group_df[group_df['Minutes played'] >= min_minutes].copy()
        xy_df = xy_df[['Player', x_metric, y_metric]].dropna()

        if len(xy_df) < 2:
            st.warning("No hay suficientes datos para generar el gráfico. Prueba reducir los minutos mínimos.")
        else:
            fig_xy = create_xy_chart(xy_df, x_metric, y_metric, selected_player,
                                     x_label=translate(x_metric),
                                     y_label=translate(y_metric))
            st.pyplot(fig_xy)

            # Download button
            buf = io.BytesIO()
            fig_xy.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                           facecolor=fig_xy.get_facecolor())
            st.download_button("⬇️ Descargar PNG", buf.getvalue(),
                               file_name="grafico_xy.png", mime="image/png")

# ---- Tab 3: Radar Pizza ---------------------------------------------------
with tab_radar:
    st.subheader(f"Radar — {selected_player}")

    # Minutes slider (same concept as Tab 2)
    radar_min_min = int(group_df['Minutes played'].min()) if 'Minutes played' in group_df.columns else 0
    radar_max_min = int(group_df['Minutes played'].max()) if 'Minutes played' in group_df.columns else 100
    radar_min_minutes = st.slider(
        "Minutos mínimos jugados", radar_min_min, radar_max_min,
        value=min(200, radar_max_min), key="radar_min_minutes"
    )

    # Filter group by minutes for min/max reference ranges
    radar_group_df = group_df[group_df['Minutes played'] >= radar_min_minutes].copy()

    player_row = radar_group_df[radar_group_df['Player'] == selected_player]
    if player_row.empty:
        st.warning("El jugador seleccionado no cumple el filtro de minutos mínimos. Reduce el slider.")
    else:
        # Build param list: defense + attack + distribution (same for all groups)
        all_radar = (RADAR_METRICS['Defensa'] + RADAR_METRICS['Ataque']
                     + RADAR_METRICS['Distribución'])

        available_params = []
        display_params = []
        for p in all_radar:
            if p in radar_group_df.columns:
                available_params.append(p)
                display_params.append(translate(p))

        if len(available_params) < 3:
            st.warning("No hay suficientes métricas disponibles.")
        else:
            player_data = player_row.iloc[0]
            values = []
            min_range = []
            max_range = []
            for p in available_params:
                col = pd.to_numeric(radar_group_df[p], errors='coerce')
                val = pd.to_numeric(player_data[p], errors='coerce')
                values.append(round(float(val), 2) if pd.notnull(val) else 0)
                mn = float(col.min()) if pd.notnull(col.min()) else 0
                mx = float(col.max()) if pd.notnull(col.max()) else 1
                if mn == mx:
                    mx = mn + 1
                min_range.append(mn)
                max_range.append(mx)

            team = str(player_data.get('Team within selected timeframe', ''))
            n_players = len(radar_group_df)
            subtitle = f"Entre {n_players} {selected_group.lower()}s | Apertura 2026"

            fig_pizza = create_pizza_chart(
                player_name=selected_player,
                player_team=team,
                subtitle=subtitle,
                params=display_params,
                values=values,
                min_range=min_range,
                max_range=max_range,
            )
            st.pyplot(fig_pizza)

            buf2 = io.BytesIO()
            fig_pizza.savefig(buf2, format='png', dpi=200, bbox_inches='tight',
                              facecolor=fig_pizza.get_facecolor())
            st.download_button("⬇️ Descargar PNG", buf2.getvalue(),
                               file_name="radar_pizza.png", mime="image/png",
                               key="dl_pizza")
