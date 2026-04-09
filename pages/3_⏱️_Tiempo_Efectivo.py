import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import timedelta

st.set_page_config(page_title="Tiempo Efectivo de Juego", layout="wide")

# ── Configuración de la app ──────────────────────────────────────────────────
APP_DIR = Path(__file__).parent.parent
DATA_DIR = APP_DIR / 'data'

# ── Logo ─────────────────────────────────────────────────────────────────────
LOGO_NEGRO = APP_DIR / 'assets' / 'logo_negro.png'
LOGO_BLANCO = APP_DIR / 'assets' / 'logo_blanco.png'

# ── Funciones ────────────────────────────────────────────────────────────────
def load_club_data(club_name):
    """Carga datos de un club específico."""
    file_pattern = f"Team Stats {club_name}.xlsx"
    file_path = DATA_DIR / file_pattern
    if file_path.exists():
        return pd.read_excel(file_path)
    return None

def calculate_effective_playing_time():
    """
    Calcula el tiempo efectivo de juego para todos los clubes.

    Fórmula:
    - Tiempo Efectivo (min) = Passes / Match Tempo
    - % Tenencia = (Tiempo Efectivo / Duración Promedio) * 100
    """
    team_files = sorted([f for f in os.listdir(DATA_DIR)
                        if f.startswith('Team Stats') and f.endswith('.xlsx')])

    results = []

    for file in team_files:
        filepath = DATA_DIR / file
        df = pd.read_excel(filepath)

        # Extraer nombre del club
        club_name = file.replace('Team Stats ', '').replace('.xlsx', '')

        # Filtrar datos válidos
        valid_data = df[
            (df['Passes / accurate'].notna()) &
            (df['Match tempo'].notna()) &
            (df['Duration'].notna())
        ].copy()

        if len(valid_data) > 0:
            # Calcular tiempo efectivo
            valid_data['Tiempo Efectivo'] = valid_data['Passes / accurate'] / valid_data['Match tempo']

            # Calcular promedios
            avg_tiempo_efectivo = valid_data['Tiempo Efectivo'].mean()
            avg_duration = valid_data['Duration'].mean()
            pct_tenencia = (avg_tiempo_efectivo / avg_duration) * 100

            # Convertir minutos decimales a formato HH:MM:SS
            td = timedelta(minutes=avg_tiempo_efectivo)
            tiempo_formato = str(td).split('.')[0]

            results.append({
                'Club': club_name,
                'Partidos': len(valid_data),
                'Tiempo Efectivo': tiempo_formato,
                'Tiempo (min)': round(avg_tiempo_efectivo, 2),
                'Duración Promedio (min)': round(avg_duration, 2),
                '% Tenencia': round(pct_tenencia, 2),
            })

    # Crear DataFrame y ordenar
    resultado_df = pd.DataFrame(results).sort_values(
        'Tiempo (min)',
        ascending=False
    ).reset_index(drop=True)
    resultado_df.index += 1

    # Retornar solo las columnas que se mostrarán al usuario
    return resultado_df[['Club', 'Partidos', 'Tiempo Efectivo', 'Duración Promedio (min)', '% Tenencia']]

# ── Encabezado ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
            border-left: 4px solid #38bdf8;
            border-radius: 8px;
            padding: 16px 22px;
            margin-bottom: 18px;">
    <div style="font-size:24px; font-weight:800; color:#f1f5f9; letter-spacing:1px;">
        ⏱️ TIEMPO EFECTIVO DE JUEGO
    </div>
    <div style="font-size:13px; color:#94a3b8; margin-top:4px;">
        Análisis de posesión real basado en pases y tempo de partido
    </div>
</div>
""", unsafe_allow_html=True)

# ── Carga y cálculo de datos ─────────────────────────────────────────────────
st.markdown("""
<p style='font-size:0.9rem; color:#9ca3af; margin-bottom:12px;'>
    <b>Metodología:</b> Tiempo Efectivo = Total de Pases ÷ Tempo del Partido
</p>
""", unsafe_allow_html=True)

# Calcular ranking
ranking = calculate_effective_playing_time()

# ── Tabla de ranking ─────────────────────────────────────────────────────────
st.subheader("Ranking por Tiempo Efectivo de Juego")

# Mostrar tabla con formato especial
st.dataframe(
    ranking,
    use_container_width=True,
    hide_index=False,
    column_config={
        "Club": st.column_config.TextColumn("Club", width="medium"),
        "Partidos": st.column_config.NumberColumn("Partidos", format="%d"),
        "Tiempo Efectivo": st.column_config.TextColumn("Tiempo Efectivo", width="medium"),
        "Duración Promedio (min)": st.column_config.NumberColumn("Duración Promedio (min)", format="%.2f"),
        "% Tenencia": st.column_config.NumberColumn("% Tenencia", format="%.2f%%"),
    }
)

# ── Explicación ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
### 📊 Interpretación de Métricas

**Tiempo Efectivo (min):** Minutos equivalentes de posesión real basados en pases y tempo
- Mayor tiempo = Mayor control del balón en juego

**Duración Promedio (min):** Promedio de duración de los partidos analizados

**% Tenencia:** Porcentaje del tiempo de partido dedicado a posesión efectiva
- Calculado como: (Tiempo Efectivo / Duración Promedio) × 100

---

**Fuente de datos:** Estadísticas oficiales de clubes - Apertura 2026
""")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("⏱️ Tiempo Efectivo de Juego · Marca Zonal · Análisis Pure Possession")
