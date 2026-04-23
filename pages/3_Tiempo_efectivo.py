import base64
import re
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Tiempo efectivo", layout="wide")

APP_DIR = Path(__file__).parent.parent
DATA_DIR = APP_DIR / "data"
ASSETS_DIR = APP_DIR / "assets"

TEAM_FILE_PREFIX = "Team Stats "
TEAM_REQUIRED_COLUMNS = {"Date", "Match", "Team", "Duration", "Passes / accurate", "Match tempo"}


def _normalize_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text)


def _team_name_from_file(path: Path) -> str:
    return path.stem.replace(TEAM_FILE_PREFIX, "", 1)


def _load_logo_base64() -> str:
    for name in ("logo_blanco.png", "logo_negro.png"):
        path = ASSETS_DIR / name
        if path.exists():
            return base64.b64encode(path.read_bytes()).decode()
    return ""


def _format_minutes_to_hhmmss(minutes_value) -> str:
    total_seconds = int(round(float(minutes_value) * 60))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _format_minutes_to_mmss(minutes_value) -> str:
    total_seconds = int(round(float(minutes_value) * 60))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def _parse_match_teams(match_text: str):
    text = str(match_text).strip()
    pattern = r"^(.*?)\s*-\s*(.*?)\s+\d+:\d+$"
    found = re.match(pattern, text)
    if not found:
        return None, None
    return found.group(1).strip(), found.group(2).strip()


def _extract_opponent(match_text: str, team_name: str) -> str:
    home, away = _parse_match_teams(match_text)
    if not home or not away:
        return "Rival desconocido"

    norm_team = _normalize_text(team_name)
    if _normalize_text(home) == norm_team:
        return away
    if _normalize_text(away) == norm_team:
        return home
    return away


@st.cache_data(show_spinner=False)
def load_effective_time_data():
    team_files = sorted(DATA_DIR.glob("Team Stats *.xlsx"))

    ranking_rows = []
    team_match_map = {}

    for path in team_files:
        club_name = _team_name_from_file(path)
        df = pd.read_excel(path)

        if not TEAM_REQUIRED_COLUMNS.issubset(df.columns):
            continue

        valid = df[list(TEAM_REQUIRED_COLUMNS)].copy()
        valid = valid.dropna(subset=["Date", "Match", "Team", "Duration", "Passes / accurate", "Match tempo"])

        valid["Date"] = pd.to_datetime(valid["Date"], errors="coerce")
        valid["Duration"] = pd.to_numeric(valid["Duration"], errors="coerce")
        valid["Passes / accurate"] = pd.to_numeric(valid["Passes / accurate"], errors="coerce")
        valid["Match tempo"] = pd.to_numeric(valid["Match tempo"], errors="coerce")
        valid = valid.dropna(subset=["Date", "Duration", "Passes / accurate", "Match tempo"])
        valid = valid[valid["Match tempo"] > 0].copy()

        valid["Tiempo efectivo equipo (min)"] = valid["Passes / accurate"] / valid["Match tempo"]

        team_rows = valid[valid["Team"].map(_normalize_text) == _normalize_text(club_name)].copy()
        if team_rows.empty:
            team_rows = valid.drop_duplicates(subset=["Date", "Match"], keep="first").copy()

        match_rows = []
        grouped_matches = valid.groupby(["Date", "Match"], sort=True, dropna=False)
        for (match_date, match_name), match_group in grouped_matches:
            if not (match_group["Team"].map(_normalize_text) == _normalize_text(club_name)).any():
                continue

            club_row = match_group[match_group["Team"].map(_normalize_text) == _normalize_text(club_name)].head(1)
            if club_row.empty:
                continue

            total_minutes = float(match_group["Duration"].dropna().iloc[0])
            effective_total = float(match_group["Tiempo efectivo equipo (min)"].sum())
            rival = _extract_opponent(match_name, club_name)

            match_rows.append(
                {
                    "Date": match_date,
                    "Match": match_name,
                    "Rival": rival,
                    "Minutos totales": total_minutes,
                    "Tiempo total corto": _format_minutes_to_mmss(total_minutes),
                    "Tiempo efectivo (min)": effective_total,
                    "Tiempo efectivo": _format_minutes_to_hhmmss(effective_total),
                    "Tiempo efectivo corto": _format_minutes_to_mmss(effective_total),
                }
            )

        team_match_df = pd.DataFrame(match_rows).sort_values(["Date", "Match"]).reset_index(drop=True)
        team_match_df["Partido"] = range(1, len(team_match_df) + 1)
        team_match_df["Fecha"] = team_match_df["Date"].dt.strftime("%d/%m/%Y")

        team_match_map[club_name] = team_match_df[
            [
                "Partido",
                "Fecha",
                "Rival",
                "Match",
                "Minutos totales",
                "Tiempo total corto",
                "Tiempo efectivo",
                "Tiempo efectivo corto",
                "Tiempo efectivo (min)",
            ]
        ].copy()

        ranking_rows.append(
            {
                "Equipo": club_name,
                "Partidos": len(team_rows),
                "Tiempo efectivo promedio (min)": team_rows["Tiempo efectivo equipo (min)"].mean(),
            }
        )

    ranking_df = pd.DataFrame(ranking_rows)
    if ranking_df.empty:
        return ranking_df, team_match_map

    ranking_df["Tiempo efectivo"] = ranking_df["Tiempo efectivo promedio (min)"].apply(_format_minutes_to_hhmmss)
    ranking_df = ranking_df.sort_values(
        "Tiempo efectivo promedio (min)", ascending=False
    ).reset_index(drop=True)

    return ranking_df, team_match_map


def _render_ranking_chart(ranking_df: pd.DataFrame):
    plot_df = ranking_df.sort_values("Tiempo efectivo promedio (min)", ascending=True)

    fig_h = max(5.5, len(plot_df) * 0.55)
    fig, ax = plt.subplots(figsize=(11, fig_h), facecolor="#0f172a")
    ax.set_facecolor("#0f172a")

    bars = ax.barh(
        plot_df["Equipo"],
        plot_df["Tiempo efectivo promedio (min)"],
        color="#22c55e",
        edgecolor="#86efac",
        linewidth=1.1,
        height=0.68,
    )

    for bar, hhmmss, mins in zip(bars, plot_df["Tiempo efectivo"], plot_df["Tiempo efectivo promedio (min)"]):
        x = bar.get_width()
        ax.text(
            x + 0.35,
            bar.get_y() + bar.get_height() / 2,
            f"{hhmmss}  |  {mins:.1f} min",
            va="center",
            ha="left",
            fontsize=10.5,
            color="#e2e8f0",
            fontweight="bold",
        )

    ax.set_title(
        "Tiempo efectivo promedio por partido",
        color="#f8fafc",
        fontsize=16,
        fontweight="bold",
        pad=16,
    )
    ax.set_xlabel("Minutos de tiempo efectivo", color="#cbd5e1", fontsize=11, labelpad=10)
    ax.tick_params(axis="x", colors="#94a3b8", labelsize=10)
    ax.tick_params(axis="y", colors="#f8fafc", labelsize=11)
    ax.grid(axis="x", color="#334155", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def _render_simple_table(df: pd.DataFrame):
    headers = "".join(f"<th>{col}</th>" for col in df.columns)
    rows = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{row[col]}</td>" for col in df.columns)
        rows.append(f"<tr>{cells}</tr>")

    st.markdown(
        f"""
        <div class="te-table-wrap">
            <table class="te-table">
                <thead><tr>{headers}</tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_match_cards(matches_df: pd.DataFrame):
    for _, row in matches_df.iterrows():
        total_minutes = float(row["Minutos totales"])
        effective_minutes = float(row["Tiempo efectivo (min)"])
        width_pct = 0 if total_minutes <= 0 else max(0.0, min(100.0, effective_minutes / total_minutes * 100))

        st.markdown(
            f"""
            <div class="te-match-card">
                <div class="te-match-top">
                    <div>
                        <div class="te-match-kicker">Fecha {int(row["Partido"])} · {row["Fecha"]}</div>
                        <div class="te-match-title">vs {row["Rival"]}</div>
                    </div>
                    <div class="te-match-badge">Tiempo efectivo {row["Tiempo efectivo corto"]}</div>
                </div>
                <div class="te-bar-wrap">
                    <div class="te-bar-base"></div>
                    <div class="te-bar-effective" style="width:{width_pct:.2f}%;"></div>
                </div>
                <div class="te-match-bottom">
                    <div class="te-match-meta">Porcentaje jugado: {width_pct:.1f}%</div>
                    <div class="te-match-badge te-match-badge-dark">Tiempo total {row["Tiempo total corto"]}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


ranking_df, team_match_map = load_effective_time_data()
logo_b64 = _load_logo_base64()
logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" alt="Marca Zonal" class="te-header-logo">'
    if logo_b64 else ""
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cousine:wght@400;700&family=Poppins:wght@600;700;800&display=swap');

html, body, *, [class*="css"], [class*="st-"], button, input, select, textarea, label {
    font-family: 'Cousine', monospace !important;
}

h1, h2, h3 {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
header { visibility: hidden; }

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1100px !important;
}

[data-testid="stMarkdownContainer"] p {
    color: #cbd5e1;
}

[data-baseweb="tab-list"] {
    gap: 10px;
}

[data-baseweb="tab"] {
    background: rgba(30, 41, 59, 0.7);
    border-radius: 12px 12px 0 0;
    padding: 10px 16px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    color: #cbd5e1 !important;
}

[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(34, 197, 94, 0.12);
    border-color: rgba(34, 197, 94, 0.45);
    color: #f8fafc !important;
}

div[data-baseweb="select"] > div {
    background: rgba(15, 23, 42, 0.85) !important;
    border: 1px solid rgba(34, 197, 94, 0.22) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}

.te-table-wrap {
    overflow-x: auto;
    margin-top: 12px;
}

.te-table {
    width: 100%;
    border-collapse: collapse;
    color: #e2e8f0;
    background: #0f172a;
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(34, 197, 94, 0.14);
}

.te-table th {
    text-align: left;
    background: #111827;
    color: #cbd5e1;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 12px 14px;
}

.te-table td {
    padding: 12px 14px;
    border-top: 1px solid rgba(148, 163, 184, 0.12);
    font-size: 0.92rem;
}

.te-match-card {
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.96) 0%, rgba(17, 24, 39, 0.96) 100%);
    border-radius: 18px;
    padding: 18px 20px 16px;
    margin-bottom: 16px;
    border: 1px solid rgba(34, 197, 94, 0.16);
    box-shadow: 0 14px 26px rgba(15, 23, 42, 0.22);
    position: relative;
    overflow: hidden;
}

.te-match-top, .te-match-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
}

.te-match-bottom {
    margin-top: 12px;
}

.te-match-kicker {
    color: #94a3b8;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.te-match-title {
    color: #f8fafc;
    font-family: 'Poppins', sans-serif !important;
    font-size: 1.12rem;
    font-weight: 700;
    margin-top: 2px;
}

.te-match-meta {
    color: #94a3b8;
    font-size: 0.85rem;
}

.te-match-badge {
    display: inline-block;
    background: rgba(34, 197, 94, 0.12);
    color: #86efac;
    padding: 8px 12px;
    border-radius: 10px;
    font-size: 0.98rem;
    white-space: nowrap;
    border: 1px solid rgba(34, 197, 94, 0.18);
}

.te-match-badge-dark {
    background: rgba(148, 163, 184, 0.10);
    color: #e2e8f0;
    border-color: rgba(148, 163, 184, 0.16);
}

.te-bar-wrap {
    position: relative;
    margin-top: 14px;
    height: 38px;
}

.te-bar-base {
    position: absolute;
    left: 0;
    right: 0;
    top: 9px;
    height: 20px;
    background: rgba(148, 163, 184, 0.18);
    border-radius: 0;
}

.te-bar-effective {
    position: absolute;
    left: 0;
    top: 3px;
    height: 16px;
    background: linear-gradient(90deg, #16a34a 0%, #22c55e 100%);
    border-radius: 0;
    box-shadow: 0 0 12px rgba(34, 197, 94, 0.22);
}

.te-header-shell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
}

.te-header-copy {
    min-width: 0;
}

.te-header-title {
    font-size: 1.55rem;
    font-weight: 800;
    color: #f8fafc;
    line-height: 1.12;
    letter-spacing: 0.02em;
}

.te-header-logo {
    height: 74px;
    width: auto;
    opacity: 0.92;
    filter: drop-shadow(0 10px 18px rgba(15, 23, 42, 0.24));
}

@media (max-width: 700px) {
    .te-header-shell {
        align-items: flex-start;
        gap: 12px;
    }

    .te-header-title {
        font-size: 1.02rem;
        line-height: 1.22;
        max-width: 13rem;
    }

    .te-header-logo {
        height: 48px;
        flex-shrink: 0;
    }
}

</style>
""", unsafe_allow_html=True)

if st.button("← Volver al inicio"):
    st.switch_page("app.py")

st.markdown(f"""
<div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid rgba(34, 197, 94, 0.18);
            border-radius: 16px;
            padding: 18px 22px;
            margin-bottom: 18px;
            box-shadow: 0 18px 30px rgba(15, 23, 42, 0.18);">
    <div class="te-header-shell">
        <div class="te-header-copy">
            <div class="te-header-title">
                TIEMPO EFECTIVO DE JUEGO EN EL FUTBOL PARAGUAYO
            </div>
        </div>
        {logo_html}
    </div>
</div>
""", unsafe_allow_html=True)

if ranking_df.empty:
    st.warning("No se encontraron datos válidos para construir Tiempo efectivo.")
else:
    tab_ranking, tab_detalle = st.tabs(
        ["Ranking general", "Detalle por equipo"]
    )

    with tab_ranking:
        st.caption(
            "Orden descendente por tiempo efectivo promedio por partido. "
            "La etiqueta principal se muestra en HH:MM:SS."
        )
        _render_ranking_chart(ranking_df)

        table_df = ranking_df[["Equipo", "Partidos", "Tiempo efectivo"]].copy()
        _render_simple_table(table_df)
        st.caption("(*) Cerro Porteño y Olimpia tienen un partido menos en el conteo por suspensión. El promedio se calcula sobre los partidos efectivamente jugados.")

    with tab_detalle:
        team_options = ranking_df["Equipo"].tolist()
        selected_team = st.selectbox("Equipo", team_options, index=0, key="te_team")
        selected_matches = team_match_map[selected_team].copy()

        st.caption(
            "Partidos ordenados cronológicamente según la fecha cargada en la base. "
            "Se muestran solo minutos totales y tiempo efectivo del encuentro para el equipo seleccionado."
        )
        _render_match_cards(selected_matches)

st.caption("X: @marca_zonal | Instagram: @marca.zonal")
