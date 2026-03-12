import pandas as pd
import streamlit as st
import os

# Per-90 columns to convert to totals
PER_90_COLUMNS = [
    'Duels per 90', 'Successful defensive actions per 90', 'Defensive duels per 90',
    'Aerial duels per 90', 'Sliding tackles per 90', 'Shots blocked per 90',
    'Interceptions per 90', 'Fouls per 90', 'Yellow cards per 90', 'Red cards per 90',
    'Successful attacking actions per 90', 'Goals per 90', 'Non-penalty goals per 90',
    'xG per 90', 'Head goals per 90', 'Shots per 90', 'Assists per 90',
    'Crosses per 90', 'Crosses from left flank per 90', 'Crosses from right flank per 90',
    'Crosses to goalie box per 90', 'Dribbles per 90', 'Offensive duels per 90',
    'Touches in box per 90', 'Progressive runs per 90', 'Accelerations per 90',
    'Received passes per 90', 'Received long passes per 90', 'Fouls suffered per 90',
    'Passes per 90', 'Forward passes per 90', 'Back passes per 90', 'Lateral passes per 90',
    'Short / medium passes per 90', 'Long passes per 90', 'xA per 90',
    'Shot assists per 90', 'Second assists per 90', 'Third assists per 90',
    'Smart passes per 90', 'Key passes per 90', 'Passes to final third per 90',
    'Passes to penalty area per 90', 'Through passes per 90', 'Deep completions per 90',
    'Deep completed crosses per 90', 'Progressive passes per 90'
]

# Action-percentage pairs for calculating successful actions
ACTION_PERCENTAGE_PAIRS = {
    'Duels': 'Duels won, %',
    'Defensive duels': 'Defensive duels won, %',
    'Aerial duels': 'Aerial duels won, %',
    'Crosses': 'Accurate crosses, %',
    'Crosses from left flank': 'Accurate crosses from left flank, %',
    'Crosses from right flank': 'Accurate crosses from right flank, %',
    'Dribbles': 'Successful dribbles, %',
    'Offensive duels': 'Offensive duels won, %',
    'Passes': 'Accurate passes, %',
    'Forward passes': 'Accurate forward passes, %',
    'Back passes': 'Accurate back passes, %',
    'Lateral passes': 'Accurate lateral passes, %',
    'Short / medium passes': 'Accurate short / medium passes, %',
    'Long passes': 'Accurate long passes, %',
    'Smart passes': 'Accurate smart passes, %',
    'Passes to final third': 'Accurate passes to final third, %',
    'Passes to penalty area': 'Accurate passes to penalty area, %',
    'Through passes': 'Accurate through passes, %',
    'Progressive passes': 'Accurate progressive passes, %',
    'Shots': 'Shots on target, %',
}

# Position to group mapping
POSITION_GROUP_MAPPING = {
    'AMF': 'Delantero',
    'CF': 'Delantero',
    'RW': 'Extremo',
    'RWF': 'Extremo',
    'RAMF': 'Extremo',
    'LWF': 'Extremo',
    'LAMF': 'Extremo',
    'LW': 'Extremo',
    'RCMF': 'Volante Central',
    'LCMF': 'Volante Central',
    'RDMF': 'Volante Central',
    'LDMF': 'Volante Central',
    'DMF': 'Volante Central',
    'RWB': 'Lateral',
    'RB': 'Lateral',
    'LWB': 'Lateral',
    'LB': 'Lateral',
    'LCB': 'Central',
    'RCB': 'Central',
    'GK': 'Portero',
}


def process_database(df):
    """Process the raw database: per-90 to totals, derived columns, position groups."""
    df = df.copy()

    # Ensure 'Pie' (Foot) column is string to avoid Arrow serialization issues
    if 'Pie' in df.columns:
        df['Pie'] = df['Pie'].astype(str)

    # Clean positions - keep only the first
    df['Position'] = df['Position'].astype(str).str.split(',').str[0].str.strip()

    # Drop PAdj columns
    padj_columns = [col for col in df.columns if 'PAdj' in col]
    df = df.drop(columns=padj_columns, errors='ignore')

    # Convert per-90 to totals
    if 'Minutes played' not in df.columns:
        raise KeyError("La columna 'Minutes played' no existe en la planilla.")

    for col in PER_90_COLUMNS:
        if col in df.columns:
            total_values = (
                (pd.to_numeric(df[col], errors='coerce').fillna(0)
                 * pd.to_numeric(df['Minutes played'], errors='coerce').fillna(0)) / 90
            ).round(1)
            new_col_name = col.replace(' per 90', '')
            df[new_col_name] = total_values
            # Keep the original per-90 column (don't drop it)

    # Calculate successful actions
    for action_col, perc_col in ACTION_PERCENTAGE_PAIRS.items():
        if action_col in df.columns and perc_col in df.columns:
            if action_col == 'Shots':
                success_col_name = 'Shots on target'
            elif 'Accurate' in perc_col:
                success_col_name = f"Accurate {action_col.lower()}"
            else:
                success_col_name = f"{action_col} won"
            base = pd.to_numeric(df[action_col], errors='coerce').fillna(0)
            perc = pd.to_numeric(df[perc_col], errors='coerce').fillna(0)
            df[success_col_name] = (base * perc / 100).round(0)

    # Derived columns
    if 'Goals' in df.columns and 'xG' in df.columns:
        df['Dif G-xG'] = (
            pd.to_numeric(df['Goals'], errors='coerce').fillna(0)
            - pd.to_numeric(df['xG'], errors='coerce').fillna(0)
        ).round(2)

    if 'Accurate progressive passes' in df.columns and 'Progressive runs' in df.columns:
        df['Progressive actions'] = (
            pd.to_numeric(df['Accurate progressive passes'], errors='coerce').fillna(0)
            + pd.to_numeric(df['Progressive runs'], errors='coerce').fillna(0)
        ).round(0)

    if 'Successful defensive actions' in df.columns and 'Successful attacking actions' in df.columns:
        df['Off Def Successful actions'] = (
            pd.to_numeric(df['Successful defensive actions'], errors='coerce').fillna(0)
            + pd.to_numeric(df['Successful attacking actions'], errors='coerce').fillna(0)
        ).round(0)

    if all(col in df.columns for col in ['Sliding tackles', 'Interceptions', 'Shots blocked']):
        df['CBIT'] = (
            pd.to_numeric(df['Sliding tackles'], errors='coerce').fillna(0)
            + pd.to_numeric(df['Interceptions'], errors='coerce').fillna(0)
            + pd.to_numeric(df['Shots blocked'], errors='coerce').fillna(0)
        ).round(0)

    # Per-90 versions of derived count columns
    minutes = pd.to_numeric(df['Minutes played'], errors='coerce').replace(0, pd.NA)
    per90_divisor = minutes / 90
    for col in ['Shots on target', 'Dribbles won', 'Accurate passes',
                'Accurate passes to final third', 'Accurate progressive passes',
                'Duels won', 'Defensive duels won', 'Aerial duels won',
                'Offensive duels won']:
        if col in df.columns:
            df[f'{col} per 90'] = (
                pd.to_numeric(df[col], errors='coerce') / per90_divisor
            ).round(2)

    # Position groups
    df['Position Group'] = df['Position'].map(POSITION_GROUP_MAPPING)
    cols = df.columns.tolist()
    if 'Position' in cols and 'Position Group' in cols:
        pos_idx = cols.index('Position')
        cols.insert(pos_idx + 1, cols.pop(cols.index('Position Group')))
        df = df[cols]

    return df


@st.cache_data
def load_and_process_data():
    """Load database.xlsx and process it. Cached by Streamlit."""
    # Try multiple paths for flexibility (local dev vs deployed)
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'database.xlsx'),
        os.path.join('data', 'database.xlsx'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_excel(path)
            return process_database(df)
    raise FileNotFoundError("database.xlsx not found in data/ directory")
