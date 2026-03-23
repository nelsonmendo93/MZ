import streamlit as st
import pandas as pd
import numpy as np
import re
import os
import sys as _sys
import math
import base64

# ── Rutas: este archivo vive en pages/, la raíz está un nivel arriba ────────
_PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_PAGE_DIR)
if _ROOT_DIR not in _sys.path:
    _sys.path.insert(0, _ROOT_DIR)
from utils.counter import count_visit

# Poisson PMF implementado con numpy puro (sin scipy)
def poisson_pmf(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_APP_DIR    = _ROOT_DIR
DATA_FOLDER = os.path.join(_ROOT_DIR, "data")
LOGO_PATH   = os.path.join(_ROOT_DIR, "assets", "logo_blanco.png")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Predictor | Marca Zonal",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS — mismo diseño que Marca Zonal
# ---------------------------------------------------------------------------
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

/* Hide sidebar and top bar */
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* Main container */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* Header area */
.mz-header {
    text-align: center;
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid rgba(14, 165, 233, 0.2);
    margin-bottom: 2rem;
}

.mz-portal-label {
    font-family: 'Cousine', monospace !important;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #0ea5e9;
    margin: 0.8rem 0 0.2rem 0;
}

.mz-title {
    font-family: 'Poppins', sans-serif !important;
    font-size: 1.6rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0;
    letter-spacing: 1px;
}

/* VS label */
.vs-label {
    font-family: 'Poppins', sans-serif !important;
    font-size: 2rem;
    font-weight: 700;
    color: #0ea5e9;
    text-align: center;
    line-height: 1;
    padding-top: 1.8rem;
}

/* Result cards */
.result-card {
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.10), rgba(6, 182, 212, 0.04));
    border: 1px solid rgba(14, 165, 233, 0.25);
    border-radius: 14px;
    padding: 1.4rem 1rem;
    text-align: center;
    margin: 0.4rem;
}

.result-card-win {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.14), rgba(16, 185, 129, 0.05));
    border: 1px solid rgba(34, 197, 94, 0.35);
    border-radius: 14px;
    padding: 1.4rem 1rem;
    text-align: center;
    margin: 0.4rem;
}

.result-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 0.5rem;
}

.result-pct {
    font-family: 'Poppins', sans-serif !important;
    font-size: 2.6rem;
    font-weight: 700;
    color: #e2e8f0;
    line-height: 1;
}

.result-pct-win {
    font-family: 'Poppins', sans-serif !important;
    font-size: 2.6rem;
    font-weight: 700;
    color: #22c55e;
    line-height: 1;
}

.result-sublabel {
    font-size: 0.72rem;
    color: #64748b;
    margin-top: 0.3rem;
}

/* Section headers */
.section-header {
    font-family: 'Cousine', monospace !important;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #0ea5e9;
    border-bottom: 1px solid rgba(14, 165, 233, 0.2);
    padding-bottom: 0.5rem;
    margin: 1.8rem 0 1rem 0;
}

/* xG cards */
.xg-card {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}

.xg-value {
    font-family: 'Poppins', sans-serif !important;
    font-size: 2rem;
    font-weight: 700;
    color: #0ea5e9;
}

.xg-label {
    font-size: 0.7rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #64748b;
    margin-top: 0.2rem;
}

/* Score table */
.score-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.55rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.3rem;
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(148, 163, 184, 0.08);
    transition: background 0.2s;
}

.score-name {
    font-family: 'Cousine', monospace !important;
    font-size: 0.92rem;
    font-weight: 700;
    color: #e2e8f0;
}

.score-pct {
    font-family: 'Poppins', sans-serif !important;
    font-size: 0.95rem;
    font-weight: 700;
    color: #0ea5e9;
}

/* Form bar */
.form-bar-container {
    height: 6px;
    background: rgba(148, 163, 184, 0.15);
    border-radius: 3px;
    overflow: hidden;
    margin-top: 0.6rem;
}

.form-bar-fill {
    height: 100%;
    border-radius: 3px;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(6, 182, 212, 0.04));
    border: 1px solid rgba(14, 165, 233, 0.2);
    border-radius: 12px;
    padding: 14px 18px;
}

/* Selectbox */
.stSelectbox label {
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #94a3b8 !important;
}

/* Divider */
hr {
    border-color: rgba(14, 165, 233, 0.15) !important;
    margin: 1.5rem 0 !important;
}

/* Selectbox placeholder */
.stSelectbox [data-baseweb="select"] {
    border-radius: 8px !important;
}

/* Corners card accent */
.xg-card-corner .xg-value { color: #10b981 !important; }

/* Yellow card accent */
.xg-card-yellow .xg-value { color: #f59e0b !important; }

/* Red card accent */
.xg-card-red .xg-value { color: #ef4444 !important; }

/* Range pill */
.range-pill {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.1);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin-bottom: 0.35rem;
}

/* Red probability blocks */
.red-block {
    border-radius: 12px;
    padding: 1.1rem 0.8rem;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading & match parsing
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_all_matches():
    files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("Team Stats") and f.endswith(".xlsx")])
    all_dfs = []
    for fname in files:
        try:
            df = pd.read_excel(os.path.join(DATA_FOLDER, fname), header=0, skiprows=[1, 2])
            df = df.dropna(subset=["Match"])
            all_dfs.append(df)
        except Exception:
            continue
    combined = pd.concat(all_dfs, ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    return combined


def parse_all_matches(combined):
    rows = []
    seen = set()
    for _, row in combined.iterrows():
        m = str(row["Match"])
        score = re.search(r"(\d+):(\d+)", m)
        if not score:
            continue
        hg, ag = int(score.group(1)), int(score.group(2))
        teams_part = m[: score.start()].strip()
        parts = teams_part.split(" - ")
        if len(parts) != 2:
            continue
        home, away = parts[0].strip(), parts[1].strip()
        key = (str(row["Date"]).split()[0], row["Match"])
        if key in seen:
            continue
        seen.add(key)

        match_rows = combined[(combined["Match"] == row["Match"]) & (combined["Date"] == row["Date"])]
        home_row = match_rows[match_rows["Team"] == home]
        away_row = match_rows[match_rows["Team"] == away]
        if home_row.empty or away_row.empty:
            continue
        h = home_row.iloc[0]
        a = away_row.iloc[0]

        rows.append({
            "date": row["Date"],
            "home_team": home,
            "away_team": away,
            "home_goals": hg,
            "away_goals": ag,
            "result": "H" if hg > ag else ("D" if hg == ag else "A"),
            "h_xg": float(h["xG"]),
            "a_xg": float(a["xG"]),
            "h_ppda": float(h["PPDA"]) if pd.notna(h["PPDA"]) else 10.0,
            "a_ppda": float(a["PPDA"]) if pd.notna(a["PPDA"]) else 10.0,
            "h_poss": float(h["Possession, %"]),
            "a_poss": float(a["Possession, %"]),
            "h_shots_total":      float(h["Shots / on target"])          if pd.notna(h["Shots / on target"])          else 0,
            "a_shots_total":      float(a["Shots / on target"])          if pd.notna(a["Shots / on target"])          else 0,
            "h_shots_ot":         float(h["Unnamed: 9"])                 if pd.notna(h["Unnamed: 9"])                 else 0,
            "a_shots_ot":         float(a["Unnamed: 9"])                 if pd.notna(a["Unnamed: 9"])                 else 0,
            "h_shot_acc":         float(h["Unnamed: 10"])                if pd.notna(h["Unnamed: 10"])                else 0,
            "a_shot_acc":         float(a["Unnamed: 10"])                if pd.notna(a["Unnamed: 10"])                else 0,
            "h_shot_distance":    float(h["Average shot distance"])      if pd.notna(h["Average shot distance"])      else 0,
            "a_shot_distance":    float(a["Average shot distance"])      if pd.notna(a["Average shot distance"])      else 0,
            "h_shots_against":    float(h["Shots against / on target"])  if pd.notna(h["Shots against / on target"]) else 0,
            "a_shots_against":    float(a["Shots against / on target"])  if pd.notna(a["Shots against / on target"]) else 0,
            "h_shots_against_ot": float(h["Unnamed: 62"])                if pd.notna(h["Unnamed: 62"])                else 0,
            "a_shots_against_ot": float(a["Unnamed: 62"])                if pd.notna(a["Unnamed: 62"])                else 0,
            "h_pass_acc":      float(h["Unnamed: 13"])               if pd.notna(h["Unnamed: 13"])               else 0.0,
            "a_pass_acc":      float(a["Unnamed: 13"])               if pd.notna(a["Unnamed: 13"])               else 0.0,
            "h_off_duel_pct":  float(h["Unnamed: 58"])               if pd.notna(h["Unnamed: 58"])               else 0.0,
            "a_off_duel_pct":  float(a["Unnamed: 58"])               if pd.notna(a["Unnamed: 58"])               else 0.0,
            "h_def_duel_pct":  float(h["Unnamed: 66"])               if pd.notna(h["Unnamed: 66"])               else 0.0,
            "a_def_duel_pct":  float(a["Unnamed: 66"])               if pd.notna(a["Unnamed: 66"])               else 0.0,
            "h_touches_pa":    float(h["Touches in penalty area"])   if pd.notna(h["Touches in penalty area"])   else 0.0,
            "a_touches_pa":    float(a["Touches in penalty area"])   if pd.notna(a["Touches in penalty area"])   else 0.0,
            "h_corners": float(h["Corners / with shots"]) if pd.notna(h["Corners / with shots"]) else 4.0,
            "a_corners": float(a["Corners / with shots"]) if pd.notna(a["Corners / with shots"]) else 4.0,
            "h_yellows": float(h["Yellow cards"]) if pd.notna(h["Yellow cards"]) else 2.0,
            "a_yellows": float(a["Yellow cards"]) if pd.notna(a["Yellow cards"]) else 2.0,
            "h_reds":    float(h["Red cards"])    if pd.notna(h["Red cards"])    else 0.0,
            "a_reds":    float(a["Red cards"])    if pd.notna(a["Red cards"])    else 0.0,
            "h_fouls":   float(h["Fouls"])        if pd.notna(h["Fouls"])        else 12.0,
            "a_fouls":   float(a["Fouls"])        if pd.notna(a["Fouls"])        else 12.0,
        })

    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Prediction engine
# ---------------------------------------------------------------------------
def _build_stats_row(r, is_home):
    """Extrae las métricas de una fila según si el equipo jugó de local o visitante."""
    return {
        "xg_scored":      r["h_xg"]            if is_home else r["a_xg"],
        "xg_conceded":    r["a_xg"]            if is_home else r["h_xg"],
        "goals_scored":   r["home_goals"]      if is_home else r["away_goals"],
        "goals_conceded": r["away_goals"]      if is_home else r["home_goals"],
        "ppda":           r["h_ppda"]          if is_home else r["a_ppda"],
        "poss":           r["h_poss"]          if is_home else r["a_poss"],
        "shots_total":      r["h_shots_total"]      if is_home else r["a_shots_total"],
        "shots_ot":         r["h_shots_ot"]         if is_home else r["a_shots_ot"],
        "shot_acc":         r["h_shot_acc"]         if is_home else r["a_shot_acc"],
        "shot_distance":    r["h_shot_distance"]    if is_home else r["a_shot_distance"],
        "shots_against":    r["h_shots_against"]    if is_home else r["a_shots_against"],
        "shots_against_ot": r["h_shots_against_ot"] if is_home else r["a_shots_against_ot"],
        "pass_acc":         r["h_pass_acc"]         if is_home else r["a_pass_acc"],
        "off_duel_pct":     r["h_off_duel_pct"]     if is_home else r["a_off_duel_pct"],
        "def_duel_pct":     r["h_def_duel_pct"]     if is_home else r["a_def_duel_pct"],
        "touches_pa":       r["h_touches_pa"]       if is_home else r["a_touches_pa"],
        "corners": r["h_corners"]  if is_home else r["a_corners"],
        "yellows": r["h_yellows"]  if is_home else r["a_yellows"],
        "reds":    r["h_reds"]     if is_home else r["a_reds"],
        "fouls":   r["h_fouls"]    if is_home else r["a_fouls"],
        "won":  (r["result"] == "H") if is_home else (r["result"] == "A"),
        "drew": r["result"] == "D",
    }


def _recency_weights(n):
    """
    Pesos decrecientes por recencia para n partidos.
    El partido más reciente recibe el mayor peso.
    Últimos 5: [0.08, 0.12, 0.20, 0.25, 0.35] (de más antiguo a más reciente).
    Partidos anteriores al 5º: peso fijo = 0.04 (normalizado después).
    """
    RECENT = [0.08, 0.12, 0.20, 0.25, 0.35]
    if n <= 5:
        w = RECENT[5 - n:]
    else:
        extra = n - 5
        w = [0.04] * extra + RECENT
    total = sum(w)
    return np.array([x / total for x in w])


def _aggregate_form(s, weights):
    """Calcula promedios ponderados y totales de forma."""
    def wavg(col):
        return float((s[col].values * weights).sum())
    wins   = int(s["won"].sum())
    draws  = int(s["drew"].sum())
    losses = len(s) - wins - draws
    return {
        "avg_xg_scored":        wavg("xg_scored"),
        "avg_xg_conceded":      wavg("xg_conceded"),
        "avg_goals_scored":     wavg("goals_scored"),
        "avg_goals_conceded":   wavg("goals_conceded"),
        "avg_ppda":             wavg("ppda"),
        "avg_poss":             wavg("poss"),
        "avg_shots_total":      wavg("shots_total"),
        "avg_shots_ot":         wavg("shots_ot"),
        "avg_shot_acc":         wavg("shot_acc"),
        "avg_shot_distance":    wavg("shot_distance"),
        "avg_shots_against":    wavg("shots_against"),
        "avg_shots_against_ot": wavg("shots_against_ot"),
        "avg_pass_acc":         wavg("pass_acc"),
        "avg_off_duel_pct":     wavg("off_duel_pct"),
        "avg_def_duel_pct":     wavg("def_duel_pct"),
        "avg_touches_pa":       wavg("touches_pa"),
        "avg_corners": wavg("corners"),
        "avg_yellows": wavg("yellows"),
        "avg_reds":    wavg("reds"),
        "avg_fouls":   wavg("fouls"),
        "wins": wins, "draws": draws, "losses": losses,
        "n": len(s),
        "form_string": "".join(["W" if r["won"] else ("D" if r["drew"] else "L") for _, r in s.iterrows()]),
    }


def get_team_form(matches_df, team, n=5):
    """Form general del equipo (local + visitante) con pesos por recencia."""
    team_matches = matches_df[
        (matches_df["home_team"] == team) | (matches_df["away_team"] == team)
    ].tail(n)
    stats = [_build_stats_row(r, r["home_team"] == team) for _, r in team_matches.iterrows()]
    if not stats:
        return {}
    s = pd.DataFrame(stats)
    return _aggregate_form(s, _recency_weights(len(s)))


def get_location_form(matches_df, team, as_home, n=5):
    """Form específica cuando el equipo juega de local o visitante."""
    if as_home:
        team_matches = matches_df[matches_df["home_team"] == team].tail(n)
    else:
        team_matches = matches_df[matches_df["away_team"] == team].tail(n)
    stats = [_build_stats_row(r, as_home) for _, r in team_matches.iterrows()]
    if not stats:
        return {}
    s = pd.DataFrame(stats)
    return _aggregate_form(s, _recency_weights(len(s)))


def predict(matches_df, home_team, away_team, n_form=5, max_goals=7):
    """
    Predicts 1/X/2 probabilities and score probabilities using a Poisson model.
    Mejoras aplicadas:
    - Form ponderada por recencia (últimos partidos pesan más)
    - Split local/visitante: se usa el rendimiento específico del equipo según condición
    - xG mezclado con goles reales (60% xG + 40% goles) para calibrar con eficiencia real
    - PPDA como ajuste de presión
    """
    # ── Form general (ponderada por recencia) ──────────────────────────────
    home_form = get_team_form(matches_df, home_team, n=n_form)
    away_form = get_team_form(matches_df, away_team, n=n_form)
    if not home_form or not away_form:
        return None

    # ── Form específica por locación ───────────────────────────────────────
    home_loc  = get_location_form(matches_df, home_team, as_home=True,  n=n_form)
    away_loc  = get_location_form(matches_df, away_team, as_home=False, n=n_form)

    LOC_BLEND = 0.65   # peso para la forma específica (local/visitante)
    MIN_LOC   = 3      # mínimo de partidos en esa condición para usar la forma específica

    def loc_or_gen(loc, gen, key):
        """Mezcla forma específica (65%) con forma general (35%) si hay suficientes datos."""
        if loc and loc.get("n", 0) >= MIN_LOC:
            return LOC_BLEND * loc[key] + (1 - LOC_BLEND) * gen[key]
        return gen[key]

    # Métricas ofensivas/defensivas mezclando locación + general
    h_xg_sc  = loc_or_gen(home_loc, home_form, "avg_xg_scored")
    h_xg_con = loc_or_gen(home_loc, home_form, "avg_xg_conceded")
    h_g_sc   = loc_or_gen(home_loc, home_form, "avg_goals_scored")
    h_g_con  = loc_or_gen(home_loc, home_form, "avg_goals_conceded")

    a_xg_sc  = loc_or_gen(away_loc, away_form, "avg_xg_scored")
    a_xg_con = loc_or_gen(away_loc, away_form, "avg_xg_conceded")
    a_g_sc   = loc_or_gen(away_loc, away_form, "avg_goals_scored")
    a_g_con  = loc_or_gen(away_loc, away_form, "avg_goals_conceded")

    # ── Blend xG + goles reales (60/40) ───────────────────────────────────
    # Combina la calidad de oportunidades (xG) con la eficiencia real del equipo.
    # Esto reduce el sesgo de penales: un equipo que acumula xG solo por penales
    # queda equilibrado por su tasa real de conversión.
    XG_W = 0.60
    GL_W = 0.40

    h_eff_sc  = XG_W * h_xg_sc  + GL_W * h_g_sc
    h_eff_con = XG_W * h_xg_con + GL_W * h_g_con
    a_eff_sc  = XG_W * a_xg_sc  + GL_W * a_g_sc
    a_eff_con = XG_W * a_xg_con + GL_W * a_g_con

    # Liga: promedios efectivos (misma mezcla para mantener consistencia de los índices)
    home_avg_eff = XG_W * matches_df["h_xg"].mean() + GL_W * matches_df["home_goals"].mean()
    away_avg_eff = XG_W * matches_df["a_xg"].mean() + GL_W * matches_df["away_goals"].mean()
    home_avg_eff = max(home_avg_eff, 0.01)
    away_avg_eff = max(away_avg_eff, 0.01)

    # ── Índices de ataque y defensa (relativos a la media de la liga) ──────
    home_attack  = h_eff_sc  / home_avg_eff
    home_defense = h_eff_con / away_avg_eff
    away_attack  = a_eff_sc  / away_avg_eff
    away_defense = a_eff_con / home_avg_eff

    # ── Lambda (goles esperados) con ventaja local ─────────────────────────
    home_advantage = 1.10
    lambda_home = home_attack * away_defense * home_avg_eff * home_advantage
    lambda_away = away_attack * home_defense * away_avg_eff

    # ── Ajuste PPDA (presión) ──────────────────────────────────────────────
    league_avg_ppda = matches_df[["h_ppda", "a_ppda"]].values.mean()
    ppda_adj_home = 1 + (league_avg_ppda - home_form["avg_ppda"]) * 0.015
    ppda_adj_away = 1 + (league_avg_ppda - away_form["avg_ppda"]) * 0.015
    lambda_away *= max(0.75, min(1.25, 1 / ppda_adj_home))
    lambda_home *= max(0.75, min(1.25, 1 / ppda_adj_away))

    lambda_home = max(0.3, min(4.5, lambda_home))
    lambda_away = max(0.3, min(4.5, lambda_away))

    # ── Matriz de marcadores (Poisson) ─────────────────────────────────────
    scores = {}
    prob_home_win = 0.0
    prob_draw     = 0.0
    prob_away_win = 0.0

    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = poisson_pmf(i, lambda_home) * poisson_pmf(j, lambda_away)
            scores[(i, j)] = p
            if i > j:   prob_home_win += p
            elif i == j: prob_draw    += p
            else:        prob_away_win += p

    total = prob_home_win + prob_draw + prob_away_win
    prob_home_win /= total
    prob_draw     /= total
    prob_away_win /= total

    total_score = sum(scores.values())
    scores = {k: v / total_score for k, v in scores.items()}

    top_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:12]

    # Marcador más probable por cada tipo de resultado
    hw_scores   = {k: v for k, v in scores.items() if k[0] > k[1]}
    draw_scores = {k: v for k, v in scores.items() if k[0] == k[1]}
    aw_scores   = {k: v for k, v in scores.items() if k[0] < k[1]}
    best_hw_score   = max(hw_scores.items(),   key=lambda x: x[1]) if hw_scores   else None
    best_draw_score = max(draw_scores.items(), key=lambda x: x[1]) if draw_scores else None
    best_aw_score   = max(aw_scores.items(),   key=lambda x: x[1]) if aw_scores   else None

    return {
        "prob_home":  prob_home_win,
        "prob_draw":  prob_draw,
        "prob_away":  prob_away_win,
        "lambda_home": lambda_home,
        "lambda_away": lambda_away,
        "top_scores":  top_scores,
        "best_hw_score":   best_hw_score,
        "best_draw_score": best_draw_score,
        "best_aw_score":   best_aw_score,
        "home_form": home_form,
        "away_form": away_form,
    }


# ---------------------------------------------------------------------------
# Corners prediction engine
# ---------------------------------------------------------------------------
def predict_corners(matches_df, home_team, away_team, n_form=5):
    """
    Predicts corner distributions using Poisson.
    Each team has a corner tendency index. Teams with high possession
    and attacking play generate more corners.
    """
    home_form = get_team_form(matches_df, home_team, n=n_form)
    away_form = get_team_form(matches_df, away_team, n=n_form)
    if not home_form or not away_form:
        return None

    league_avg_corners = (
        matches_df["h_corners"].mean() + matches_df["a_corners"].mean()
    ) / 2

    # Corner tendency: own avg corners / league avg
    h_tendency = home_form["avg_corners"] / league_avg_corners
    a_tendency = away_form["avg_corners"] / league_avg_corners

    # Possession adjustment: more possession → more corners
    league_avg_poss = 50.0
    h_poss_adj = 1 + (home_form["avg_poss"] - league_avg_poss) * 0.008
    a_poss_adj = 1 + (away_form["avg_poss"] - league_avg_poss) * 0.008

    # Slight home advantage on corners
    lambda_h = h_tendency * league_avg_corners * h_poss_adj * 1.05
    lambda_a = a_tendency * league_avg_corners * a_poss_adj

    lambda_h = max(1.0, min(10.0, lambda_h))
    lambda_a = max(1.0, min(10.0, lambda_a))

    # Score probabilities for corner combinations (0-15 per team)
    max_c = 15
    h_dist = [poisson_pmf(k, lambda_h) for k in range(max_c + 1)]
    a_dist = [poisson_pmf(k, lambda_a) for k in range(max_c + 1)]

    # Top corner combos
    combos = {}
    for i in range(max_c + 1):
        for j in range(max_c + 1):
            combos[(i, j)] = h_dist[i] * a_dist[j]
    total_c = sum(combos.values())
    combos = {k: v / total_c for k, v in combos.items()}
    top_combos = sorted(combos.items(), key=lambda x: x[1], reverse=True)[:12]

    # Total corner ranges
    ranges = {"0–5": 0, "6–8": 0, "9–11": 0, "12–14": 0, "15+": 0}
    for (i, j), p in combos.items():
        t = i + j
        if t <= 5:     ranges["0–5"]   += p
        elif t <= 8:   ranges["6–8"]   += p
        elif t <= 11:  ranges["9–11"]  += p
        elif t <= 14:  ranges["12–14"] += p
        else:          ranges["15+"]   += p

    return {
        "lambda_h": lambda_h,
        "lambda_a": lambda_a,
        "top_combos": top_combos,
        "ranges": ranges,
    }


# ---------------------------------------------------------------------------
# Cards prediction engine
# ---------------------------------------------------------------------------
def predict_cards(matches_df, home_team, away_team, n_form=5):
    """
    Predicts yellow and red card distributions using Poisson.
    Fouls tendency adjusts the yellow card lambda.
    Red cards use a low-lambda Poisson (rare events).
    """
    home_form = get_team_form(matches_df, home_team, n=n_form)
    away_form = get_team_form(matches_df, away_team, n=n_form)
    if not home_form or not away_form:
        return None

    league_avg_fouls   = (matches_df["h_fouls"].mean()   + matches_df["a_fouls"].mean())   / 2
    league_avg_yellows = (matches_df["h_yellows"].mean() + matches_df["a_yellows"].mean()) / 2
    league_avg_reds    = (matches_df["h_reds"].mean()    + matches_df["a_reds"].mean())    / 2

    # Yellow card lambda: own yellow avg × fouls ratio vs league
    h_foul_ratio = home_form["avg_fouls"] / league_avg_fouls
    a_foul_ratio = away_form["avg_fouls"] / league_avg_fouls
    lambda_yh = home_form["avg_yellows"] * h_foul_ratio
    lambda_ya = away_form["avg_yellows"] * a_foul_ratio
    lambda_yh = max(0.3, min(6.0, lambda_yh))
    lambda_ya = max(0.3, min(6.0, lambda_ya))

    # Red card lambdas (rare: clamp tightly)
    lambda_rh = max(0.02, min(0.5, home_form["avg_reds"]))
    lambda_ra = max(0.02, min(0.5, away_form["avg_reds"]))

    # Yellow combos (0–8 per team)
    max_y = 8
    yh_dist = [poisson_pmf(k, lambda_yh) for k in range(max_y + 1)]
    ya_dist = [poisson_pmf(k, lambda_ya) for k in range(max_y + 1)]
    yellow_combos = {}
    for i in range(max_y + 1):
        for j in range(max_y + 1):
            yellow_combos[(i, j)] = yh_dist[i] * ya_dist[j]
    total_y = sum(yellow_combos.values())
    yellow_combos = {k: v / total_y for k, v in yellow_combos.items()}
    top_yellow_combos = sorted(yellow_combos.items(), key=lambda x: x[1], reverse=True)[:10]

    # Total yellow ranges
    yellow_ranges = {"0–2": 0, "3–4": 0, "5–6": 0, "7+": 0}
    for (i, j), p in yellow_combos.items():
        t = i + j
        if t <= 2:    yellow_ranges["0–2"] += p
        elif t <= 4:  yellow_ranges["3–4"] += p
        elif t <= 6:  yellow_ranges["5–6"] += p
        else:         yellow_ranges["7+"]  += p

    # Red card match probabilities
    p_no_red   = poisson_pmf(0, lambda_rh) * poisson_pmf(0, lambda_ra)
    p_one_red  = (poisson_pmf(1, lambda_rh) * poisson_pmf(0, lambda_ra) +
                  poisson_pmf(0, lambda_rh) * poisson_pmf(1, lambda_ra))
    p_two_plus = 1.0 - p_no_red - p_one_red
    total_r    = p_no_red + p_one_red + p_two_plus
    p_red_home_team = poisson_pmf(1, lambda_rh) * poisson_pmf(0, lambda_ra) / total_r
    p_red_away_team = poisson_pmf(0, lambda_rh) * poisson_pmf(1, lambda_ra) / total_r

    return {
        "lambda_yh": lambda_yh,
        "lambda_ya": lambda_ya,
        "lambda_rh": lambda_rh,
        "lambda_ra": lambda_ra,
        "top_yellow_combos": top_yellow_combos,
        "yellow_ranges": yellow_ranges,
        "p_no_red":        p_no_red   / total_r,
        "p_one_red":       p_one_red  / total_r,
        "p_two_plus":      p_two_plus / total_r,
        "p_red_home_team": p_red_home_team,
        "p_red_away_team": p_red_away_team,
    }


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def logo_b64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def form_badge(char):
    colors = {"W": "#22c55e", "D": "#f59e0b", "L": "#ef4444"}
    c = colors.get(char, "#64748b")
    labels = {"W": "G", "D": "E", "L": "P"}
    return f'<span style="display:inline-block;width:22px;height:22px;border-radius:50%;background:{c};color:#fff;font-size:0.65rem;font-weight:700;text-align:center;line-height:22px;margin:0 2px;">{labels.get(char, char)}</span>'


def render_progress_bar(pct, color="#0ea5e9"):
    return f"""
    <div class="form-bar-container">
        <div class="form-bar-fill" style="width:{pct*100:.1f}%;background:{color};"></div>
    </div>"""


def result_card(label, pct, is_best=False):
    card_class = "result-card-win" if is_best else "result-card"
    pct_class = "result-pct-win" if is_best else "result-pct"
    return f"""
    <div class="{card_class}">
        <div class="result-label">{label}</div>
        <div class="{pct_class}">{pct*100:.1f}%</div>
        {render_progress_bar(pct, "#22c55e" if is_best else "#0ea5e9")}
    </div>"""


def score_result_label(i, j, home, away):
    if i > j:
        return f"<span style='color:#22c55e;font-size:0.7rem;'>▲ {home[:12]}</span>"
    elif i == j:
        return "<span style='color:#f59e0b;font-size:0.7rem;'>= Empate</span>"
    else:
        return f"<span style='color:#ef4444;font-size:0.7rem;'>▲ {away[:12]}</span>"


# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------

# Load data
try:
    raw = load_all_matches()
    matches = parse_all_matches(raw)
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

teams = sorted(set(matches["home_team"].tolist() + matches["away_team"].tolist()))

# --- BOTÓN VOLVER ---
if st.button("← Volver al inicio"):
    st.switch_page("app.py")
st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

# --- HEADER ---
logo_data = logo_b64()
logo_html = f'<img src="data:image/png;base64,{logo_data}" style="height:62px; margin-bottom:0.4rem;" />' if logo_data else ""

st.markdown(f"""
<div class="mz-header">
    {logo_html}
    <div class="mz-portal-label">Portal de datos</div>
    <div class="mz-title">Índice de Probabilidades</div>
</div>
""", unsafe_allow_html=True)

# --- TEAM SELECTORS ---
col_home, col_vs, col_away = st.columns([5, 1, 5])

with col_home:
    home_team = st.selectbox(
        "EQUIPO LOCAL",
        options=["— Seleccionar equipo —"] + teams,
        index=0,
        key="home",
    )

with col_vs:
    st.markdown('<div class="vs-label">vs</div>', unsafe_allow_html=True)

with col_away:
    away_team = st.selectbox(
        "EQUIPO VISITANTE",
        options=["— Seleccionar equipo —"] + teams,
        index=0,
        key="away",
    )

# --- VALIDATION ---
valid = (
    home_team != "— Seleccionar equipo —"
    and away_team != "— Seleccionar equipo —"
    and home_team != away_team
)

if home_team == away_team and home_team != "— Seleccionar equipo —":
    st.warning("⚠️  Seleccioná dos equipos diferentes.")

# --- PREDICTION ---
if valid:
    result = predict(matches, home_team, away_team)

    if result is None:
        st.error("No hay suficientes datos para predecir este partido.")
        st.stop()

    ph = result["prob_home"]
    pd_ = result["prob_draw"]
    pa = result["prob_away"]
    lh = result["lambda_home"]
    la = result["lambda_away"]
    hf = result["home_form"]
    af = result["away_form"]
    top_scores = result["top_scores"]
    best_hw_score   = result["best_hw_score"]
    best_draw_score = result["best_draw_score"]
    best_aw_score   = result["best_aw_score"]

    best = max(ph, pd_, pa)

    # ── 1X2 PROBABILITIES ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Probabilidades del resultado</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(result_card(f"🏠 {home_team}", ph, is_best=(ph == best)), unsafe_allow_html=True)
    with c2:
        st.markdown(result_card("⚖️ Empate", pd_, is_best=(pd_ == best)), unsafe_allow_html=True)
    with c3:
        st.markdown(result_card(f"✈️ {away_team}", pa, is_best=(pa == best)), unsafe_allow_html=True)

    # ── MARCADOR MÁS PROBABLE POR RESULTADO ───────────────────────────────
    # Muestra el marcador exacto más probable para cada tipo de resultado.
    # Resuelve la confusión cuando el marcador global más probable es empate
    # pero la victoria local sigue siendo el resultado más probable en conjunto.
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    def _score_badge(score_tuple, prob, label, color_border, color_score):
        if score_tuple is None:
            return ""
        i, j = score_tuple
        return f"""
        <div style="background:rgba(30,41,59,0.6);border:1px solid {color_border};
                    border-radius:12px;padding:0.9rem 0.6rem;text-align:center;">
            <div style="font-size:0.62rem;font-weight:700;letter-spacing:2px;
                        text-transform:uppercase;color:#64748b;margin-bottom:0.4rem;">{label}</div>
            <div style="font-family:'Poppins',sans-serif;font-size:1.9rem;font-weight:700;
                        color:{color_score};line-height:1;">{i} – {j}</div>
            <div style="font-size:0.75rem;color:#94a3b8;margin-top:0.3rem;">{prob*100:.1f}% prob.</div>
        </div>"""

    sb1, sb2, sb3 = st.columns(3)
    with sb1:
        st.markdown(_score_badge(
            best_hw_score[0] if best_hw_score else None,
            best_hw_score[1] if best_hw_score else 0,
            f"🏠 Victoria {home_team[:14]}",
            "rgba(34,197,94,0.35)", "#22c55e"
        ), unsafe_allow_html=True)
    with sb2:
        st.markdown(_score_badge(
            best_draw_score[0] if best_draw_score else None,
            best_draw_score[1] if best_draw_score else 0,
            "⚖️ Empate más probable",
            "rgba(245,158,11,0.35)", "#f59e0b"
        ), unsafe_allow_html=True)
    with sb3:
        st.markdown(_score_badge(
            best_aw_score[0] if best_aw_score else None,
            best_aw_score[1] if best_aw_score else 0,
            f"✈️ Victoria {away_team[:14]}",
            "rgba(239,68,68,0.35)", "#ef4444"
        ), unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.65rem;color:#475569;text-align:center;padding:0.5rem 0 0.2rem;
                letter-spacing:0.5px;">
        Marcador exacto más probable dentro de cada tipo de resultado.
        Las probabilidades de victoria suman todos los marcadores posibles de ese resultado.
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── PANEL COMPARATIVO ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">📺 Panel comparativo</div>', unsafe_allow_html=True)

    def compare_row(label, val_h, val_a, fmt="{:.1f}", higher_is_better=True, unit=""):
        """Renders a TV-broadcast-style face-to-face comparison row."""
        total = val_h + val_a
        if total == 0:
            pct_h, pct_a = 50, 50
        else:
            pct_h = val_h / total * 100
            pct_a = val_a / total * 100
        color_h = "#0ea5e9" if (val_h >= val_a) == higher_is_better else "#334155"
        color_a = "#0ea5e9" if (val_a > val_h)  == higher_is_better else "#334155"
        txt_h = fmt.format(val_h) + unit
        txt_a = fmt.format(val_a) + unit
        return f"""
        <div style="display:grid;grid-template-columns:90px 1fr 90px;align-items:center;
                    gap:0.6rem;padding:0.55rem 0.8rem;margin-bottom:0.35rem;
                    background:rgba(30,41,59,0.5);border-radius:10px;
                    border:1px solid rgba(148,163,184,0.08);">
            <div style="font-family:'Poppins',sans-serif;font-size:1.05rem;font-weight:700;
                        color:#e2e8f0;text-align:left;">{txt_h}</div>
            <div>
                <div style="font-size:0.62rem;font-weight:700;letter-spacing:1.5px;
                            text-transform:uppercase;color:#64748b;text-align:center;
                            margin-bottom:5px;">{label}</div>
                <div style="display:flex;height:7px;border-radius:4px;overflow:hidden;gap:1px;">
                    <div style="flex:{pct_h:.1f};background:{color_h};border-radius:4px 0 0 4px;
                                transition:flex 0.3s ease;"></div>
                    <div style="flex:{pct_a:.1f};background:{color_a};border-radius:0 4px 4px 0;
                                transition:flex 0.3s ease;"></div>
                </div>
            </div>
            <div style="font-family:'Poppins',sans-serif;font-size:1.05rem;font-weight:700;
                        color:#e2e8f0;text-align:right;">{txt_a}</div>
        </div>"""

    # Team name header row
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:90px 1fr 90px;gap:0.6rem;
                padding:0.3rem 0.8rem 0.5rem;">
        <div style="font-size:0.72rem;font-weight:700;letter-spacing:1.5px;
                    text-transform:uppercase;color:#0ea5e9;">{home_team}</div>
        <div></div>
        <div style="font-size:0.72rem;font-weight:700;letter-spacing:1.5px;
                    text-transform:uppercase;color:#0ea5e9;text-align:right;">{away_team}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(compare_row("Posesión", hf["avg_poss"], af["avg_poss"],
        fmt="{:.1f}", unit="%"), unsafe_allow_html=True)
    st.markdown(compare_row("Remates totales", hf["avg_shots_total"], af["avg_shots_total"],
        fmt="{:.1f}"), unsafe_allow_html=True)
    st.markdown(compare_row("Remates al arco", hf["avg_shots_ot"], af["avg_shots_ot"],
        fmt="{:.1f}"), unsafe_allow_html=True)
    st.markdown(compare_row("Precisión de pase", hf["avg_pass_acc"], af["avg_pass_acc"],
        fmt="{:.1f}", unit="%"), unsafe_allow_html=True)
    st.markdown(compare_row("Duelos ofensivos %", hf["avg_off_duel_pct"], af["avg_off_duel_pct"],
        fmt="{:.1f}", unit="%"), unsafe_allow_html=True)
    st.markdown(compare_row("Duelos defensivos %", hf["avg_def_duel_pct"], af["avg_def_duel_pct"],
        fmt="{:.1f}", unit="%"), unsafe_allow_html=True)
    st.markdown(compare_row("Toques en el área", hf["avg_touches_pa"], af["avg_touches_pa"],
        fmt="{:.1f}"), unsafe_allow_html=True)

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # ── EXPECTED GOALS ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⚽ Goles esperados</div>', unsafe_allow_html=True)

    eg1, eg2, eg3 = st.columns([4, 1, 4])
    with eg1:
        st.markdown(f"""
        <div class="xg-card">
            <div class="xg-value">{lh:.2f}</div>
            <div class="xg-label">xG {home_team}</div>
        </div>""", unsafe_allow_html=True)
    with eg2:
        st.markdown('<div style="text-align:center;padding-top:1rem;color:#475569;font-size:1.2rem;">—</div>', unsafe_allow_html=True)
    with eg3:
        st.markdown(f"""
        <div class="xg-card">
            <div class="xg-value">{la:.2f}</div>
            <div class="xg-label">xG {away_team}</div>
        </div>""", unsafe_allow_html=True)

    # ── ÍNDICE DE REMATES ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">🔫 Índice de remates</div>', unsafe_allow_html=True)

    def shot_compare_row(label, val_h, val_a, fmt="{:.1f}", higher_is_better=True, unit=""):
        """Renders a side-by-side comparison bar for a shooting metric."""
        max_val = max(val_h, val_a, 0.01)
        pct_h = val_h / max_val
        pct_a = val_a / max_val
        color_h = "#0ea5e9" if (val_h >= val_a) == higher_is_better else "#64748b"
        color_a = "#0ea5e9" if (val_a > val_h)  == higher_is_better else "#64748b"
        bar_h = f'<div style="height:5px;background:{color_h};border-radius:3px;width:{pct_h*100:.0f}%;margin-top:3px;"></div>'
        bar_a = f'<div style="height:5px;background:{color_a};border-radius:3px;width:{pct_a*100:.0f}%;margin-top:3px;"></div>'
        return f"""
        <div style="display:grid;grid-template-columns:1fr 160px 1fr;align-items:center;
                    gap:0.5rem;padding:0.5rem 0.8rem;border-radius:8px;
                    background:rgba(30,41,59,0.45);margin-bottom:0.3rem;
                    border:1px solid rgba(148,163,184,0.07);">
            <div style="text-align:left;">
                <div style="font-family:'Poppins',sans-serif;font-size:1rem;font-weight:700;
                            color:#e2e8f0;">{fmt.format(val_h)}{unit}</div>
                {bar_h}
            </div>
            <div style="text-align:center;font-size:0.65rem;font-weight:700;letter-spacing:1.5px;
                        text-transform:uppercase;color:#475569;">{label}</div>
            <div style="text-align:right;">
                <div style="font-family:'Poppins',sans-serif;font-size:1rem;font-weight:700;
                            color:#e2e8f0;">{fmt.format(val_a)}{unit}</div>
                {bar_a}
            </div>
        </div>"""

    # Team labels row
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 160px 1fr;gap:0.5rem;
                padding:0.4rem 0.8rem;margin-bottom:0.2rem;">
        <div style="font-size:0.72rem;font-weight:700;letter-spacing:1.5px;
                    text-transform:uppercase;color:#0ea5e9;">{home_team}</div>
        <div></div>
        <div style="font-size:0.72rem;font-weight:700;letter-spacing:1.5px;
                    text-transform:uppercase;color:#0ea5e9;text-align:right;">{away_team}</div>
    </div>""", unsafe_allow_html=True)

    # ── Ofensiva
    st.markdown("""<div style="font-size:0.65rem;letter-spacing:2px;color:#334155;
                text-transform:uppercase;padding:0.3rem 0.8rem 0.1rem;">⚔️ Ataque</div>""",
                unsafe_allow_html=True)
    st.markdown(shot_compare_row("Remates por partido",
        hf["avg_shots_total"], af["avg_shots_total"]), unsafe_allow_html=True)
    st.markdown(shot_compare_row("Al arco por partido",
        hf["avg_shots_ot"], af["avg_shots_ot"]), unsafe_allow_html=True)
    st.markdown(shot_compare_row("Precisión de remate",
        hf["avg_shot_acc"], af["avg_shot_acc"], fmt="{:.1f}", unit="%"), unsafe_allow_html=True)
    st.markdown(shot_compare_row("Distancia promedio",
        hf["avg_shot_distance"], af["avg_shot_distance"],
        fmt="{:.1f}", unit=" m", higher_is_better=False), unsafe_allow_html=True)

    # ── Defensiva
    st.markdown("""<div style="font-size:0.65rem;letter-spacing:2px;color:#334155;
                text-transform:uppercase;padding:0.5rem 0.8rem 0.1rem;">🛡️ Defensa</div>""",
                unsafe_allow_html=True)
    st.markdown(shot_compare_row("Remates concedidos",
        hf["avg_shots_against"], af["avg_shots_against"],
        higher_is_better=False), unsafe_allow_html=True)
    st.markdown(shot_compare_row("Al arco concedidos",
        hf["avg_shots_against_ot"], af["avg_shots_against_ot"],
        higher_is_better=False), unsafe_allow_html=True)

    # ── Possession + PPDA as context
    st.markdown("""<div style="font-size:0.65rem;letter-spacing:2px;color:#334155;
                text-transform:uppercase;padding:0.5rem 0.8rem 0.1rem;">📐 Contexto</div>""",
                unsafe_allow_html=True)
    st.markdown(shot_compare_row("Posesión promedio",
        hf["avg_poss"], af["avg_poss"], fmt="{:.1f}", unit="%"), unsafe_allow_html=True)
    st.markdown(shot_compare_row("PPDA (presión)",
        hf["avg_ppda"], af["avg_ppda"],
        fmt="{:.1f}", higher_is_better=False), unsafe_allow_html=True)

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # ── SCORE PROBABILITIES ────────────────────────────────────────────────
    st.markdown('<div class="section-header">🎯 Marcadores más probables</div>', unsafe_allow_html=True)

    sc1, sc2 = st.columns(2)
    half = len(top_scores) // 2
    for col_idx, col in enumerate([sc1, sc2]):
        with col:
            chunk = top_scores[:half] if col_idx == 0 else top_scores[half:]
            for (i, j), p in chunk:
                outcome_label = score_result_label(i, j, home_team, away_team)
                bar_color = "#22c55e" if i > j else ("#f59e0b" if i == j else "#ef4444")
                st.markdown(f"""
                <div class="score-row">
                    <div>
                        <span class="score-name">{i} – {j}</span>
                        <br/>{outcome_label}
                    </div>
                    <div style="text-align:right;">
                        <span class="score-pct">{p*100:.1f}%</span>
                        {render_progress_bar(p / top_scores[0][1], bar_color)}
                    </div>
                </div>""", unsafe_allow_html=True)

    # ── CORNERS ────────────────────────────────────────────────────────────
    cr = predict_corners(matches, home_team, away_team)
    if cr:
        st.markdown('<div class="section-header">🚩 Índice de corners</div>', unsafe_allow_html=True)

        cc1, cc2, cc3 = st.columns([4, 1, 4])
        with cc1:
            st.markdown(f"""
            <div class="xg-card xg-card-corner">
                <div class="xg-value" style="color:#10b981;">{cr['lambda_h']:.1f}</div>
                <div class="xg-label">Corners esperados · {home_team}</div>
            </div>""", unsafe_allow_html=True)
        with cc2:
            st.markdown('<div style="text-align:center;padding-top:1rem;color:#475569;font-size:1.2rem;">—</div>', unsafe_allow_html=True)
        with cc3:
            st.markdown(f"""
            <div class="xg-card xg-card-corner">
                <div class="xg-value" style="color:#10b981;">{cr['lambda_a']:.1f}</div>
                <div class="xg-label">Corners esperados · {away_team}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        cr_col1, cr_col2 = st.columns(2)

        with cr_col1:
            st.markdown(f"<div style='font-size:0.7rem;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;margin-bottom:0.5rem;'>Corners más probables</div>", unsafe_allow_html=True)
            top_cr = cr["top_combos"]
            for (i, j), p in top_cr[:6]:
                bar_w = p / top_cr[0][1]
                st.markdown(f"""
                <div class="score-row">
                    <div>
                        <span class="score-name" style="color:#10b981;">{i} – {j}</span>
                        <br/><span style="font-size:0.68rem;color:#64748b;">{home_team[:12]} · {away_team[:12]}</span>
                    </div>
                    <div style="text-align:right;">
                        <span class="score-pct" style="color:#10b981;">{p*100:.1f}%</span>
                        {render_progress_bar(bar_w, "#10b981")}
                    </div>
                </div>""", unsafe_allow_html=True)

        with cr_col2:
            st.markdown(f"<div style='font-size:0.7rem;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;margin-bottom:0.5rem;'>Total corners del partido</div>", unsafe_allow_html=True)
            max_range_p = max(cr["ranges"].values())
            for label, p in cr["ranges"].items():
                bar_w = p / max_range_p if max_range_p > 0 else 0
                st.markdown(f"""
                <div class="range-pill">
                    <span style="font-family:'Cousine',monospace;font-size:0.9rem;font-weight:700;color:#e2e8f0;">{label} corners</span>
                    <div style="text-align:right;min-width:80px;">
                        <span style="font-family:'Poppins',sans-serif;font-size:0.95rem;font-weight:700;color:#10b981;">{p*100:.1f}%</span>
                        {render_progress_bar(bar_w, "#10b981")}
                    </div>
                </div>""", unsafe_allow_html=True)

    # ── TARJETAS AMARILLAS ──────────────────────────────────────────────────
    cd = predict_cards(matches, home_team, away_team)
    if cd:
        st.markdown('<div class="section-header">🟨 Índice de tarjetas amarillas</div>', unsafe_allow_html=True)

        yc1, yc2, yc3 = st.columns([4, 1, 4])
        with yc1:
            st.markdown(f"""
            <div class="xg-card xg-card-yellow">
                <div class="xg-value" style="color:#f59e0b;">{cd['lambda_yh']:.1f}</div>
                <div class="xg-label">Amarillas esperadas · {home_team}</div>
            </div>""", unsafe_allow_html=True)
        with yc2:
            st.markdown('<div style="text-align:center;padding-top:1rem;color:#475569;font-size:1.2rem;">—</div>', unsafe_allow_html=True)
        with yc3:
            st.markdown(f"""
            <div class="xg-card xg-card-yellow">
                <div class="xg-value" style="color:#f59e0b;">{cd['lambda_ya']:.1f}</div>
                <div class="xg-label">Amarillas esperadas · {away_team}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        yc_col1, yc_col2 = st.columns(2)

        with yc_col1:
            st.markdown(f"<div style='font-size:0.7rem;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;margin-bottom:0.5rem;'>Combinaciones más probables</div>", unsafe_allow_html=True)
            top_yc = cd["top_yellow_combos"]
            for (i, j), p in top_yc[:6]:
                bar_w = p / top_yc[0][1]
                st.markdown(f"""
                <div class="score-row">
                    <div>
                        <span class="score-name" style="color:#f59e0b;">{i} – {j}</span>
                        <br/><span style="font-size:0.68rem;color:#64748b;">{home_team[:12]} · {away_team[:12]}</span>
                    </div>
                    <div style="text-align:right;">
                        <span class="score-pct" style="color:#f59e0b;">{p*100:.1f}%</span>
                        {render_progress_bar(bar_w, "#f59e0b")}
                    </div>
                </div>""", unsafe_allow_html=True)

        with yc_col2:
            st.markdown(f"<div style='font-size:0.7rem;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;margin-bottom:0.5rem;'>Total amarillas del partido</div>", unsafe_allow_html=True)
            max_yrange_p = max(cd["yellow_ranges"].values())
            for label, p in cd["yellow_ranges"].items():
                bar_w = p / max_yrange_p if max_yrange_p > 0 else 0
                st.markdown(f"""
                <div class="range-pill">
                    <span style="font-family:'Cousine',monospace;font-size:0.9rem;font-weight:700;color:#e2e8f0;">{label} amarillas</span>
                    <div style="text-align:right;min-width:80px;">
                        <span style="font-family:'Poppins',sans-serif;font-size:0.95rem;font-weight:700;color:#f59e0b;">{p*100:.1f}%</span>
                        {render_progress_bar(bar_w, "#f59e0b")}
                    </div>
                </div>""", unsafe_allow_html=True)

    # ── TARJETAS ROJAS ──────────────────────────────────────────────────────
    if cd:
        st.markdown('<div class="section-header">🟥 Índice de tarjeta roja</div>', unsafe_allow_html=True)

        rc1, rc2, rc3 = st.columns(3)
        red_cards_data = [
            ("Sin rojas", cd["p_no_red"],   "#334155", "#94a3b8"),
            ("1 roja",    cd["p_one_red"],  "#7f1d1d", "#ef4444"),
            ("2 o más",   cd["p_two_plus"], "#450a0a", "#dc2626"),
        ]
        for col, (label, prob, bg, accent) in zip([rc1, rc2, rc3], red_cards_data):
            with col:
                st.markdown(f"""
                <div class="red-block" style="background:linear-gradient(135deg,{bg}88,{bg}33);
                            border:1px solid {accent}55;">
                    <div style="font-size:0.7rem;font-weight:700;letter-spacing:2px;
                                text-transform:uppercase;color:{accent};margin-bottom:0.4rem;">{label}</div>
                    <div style="font-family:'Poppins',sans-serif;font-size:2.4rem;
                                font-weight:700;color:#e2e8f0;line-height:1;">{prob*100:.1f}%</div>
                    {render_progress_bar(prob, accent)}
                </div>""", unsafe_allow_html=True)

        if cd["p_one_red"] > 0.05:
            p_home_roja = cd["p_red_home_team"]
            p_away_roja = cd["p_red_away_team"]
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
            rc_a, rc_b = st.columns(2)
            with rc_a:
                st.markdown(f"""
                <div class="range-pill">
                    <span style="color:#e2e8f0;font-size:0.85rem;font-weight:700;">🟥 Roja para {home_team[:16]}</span>
                    <span style="color:#ef4444;font-family:'Poppins',sans-serif;font-weight:700;">{p_home_roja*100:.1f}%</span>
                </div>""", unsafe_allow_html=True)
            with rc_b:
                st.markdown(f"""
                <div class="range-pill">
                    <span style="color:#e2e8f0;font-size:0.85rem;font-weight:700;">🟥 Roja para {away_team[:16]}</span>
                    <span style="color:#ef4444;font-family:'Poppins',sans-serif;font-weight:700;">{p_away_roja*100:.1f}%</span>
                </div>""", unsafe_allow_html=True)

    # ── FORM & CONTEXT ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📈 Forma reciente (últimos 5 partidos)</div>', unsafe_allow_html=True)

    f1, f2 = st.columns(2)

    for col, team, form in [(f1, home_team, hf), (f2, away_team, af)]:
        with col:
            badges = "".join([form_badge(c) for c in form.get("form_string", "")])
            win_rate = form["wins"] / form["n"] if form["n"] > 0 else 0
            st.markdown(f"""
            <div class="result-card" style="text-align:left;padding:1.2rem 1.4rem;">
                <div style="font-family:'Poppins',sans-serif;font-weight:700;font-size:1rem;
                            color:#e2e8f0;margin-bottom:0.8rem;">{team}</div>
                <div style="margin-bottom:0.8rem;">{badges}</div>
                <div style="display:flex;gap:1.2rem;flex-wrap:wrap;">
                    <div>
                        <div style="font-size:1.3rem;font-weight:700;color:#22c55e;">{form['wins']}</div>
                        <div style="font-size:0.65rem;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;">Victorias</div>
                    </div>
                    <div>
                        <div style="font-size:1.3rem;font-weight:700;color:#f59e0b;">{form['draws']}</div>
                        <div style="font-size:0.65rem;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;">Empates</div>
                    </div>
                    <div>
                        <div style="font-size:1.3rem;font-weight:700;color:#ef4444;">{form['losses']}</div>
                        <div style="font-size:0.65rem;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;">Derrotas</div>
                    </div>
                    <div>
                        <div style="font-size:1.3rem;font-weight:700;color:#0ea5e9;">{form['avg_xg_scored']:.2f}</div>
                        <div style="font-size:0.65rem;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;">xG prom.</div>
                    </div>
                    <div>
                        <div style="font-size:1.3rem;font-weight:700;color:#a78bfa;">{form['avg_ppda']:.1f}</div>
                        <div style="font-size:0.65rem;letter-spacing:1.5px;color:#64748b;text-transform:uppercase;">PPDA</div>
                    </div>
                </div>
                {render_progress_bar(win_rate, "#22c55e")}
                <div style="font-size:0.65rem;color:#475569;margin-top:0.3rem;">Tasa de victoria: {win_rate*100:.0f}%</div>
            </div>""", unsafe_allow_html=True)

    # ── H2H ────────────────────────────────────────────────────────────────
    h2h = matches[
        ((matches["home_team"] == home_team) & (matches["away_team"] == away_team))
        | ((matches["home_team"] == away_team) & (matches["away_team"] == home_team))
    ]

    if not h2h.empty:
        st.markdown('<div class="section-header">🔁 Historial de enfrentamientos directos</div>', unsafe_allow_html=True)
        h2h_home_wins = ((h2h["home_team"] == home_team) & (h2h["result"] == "H")).sum() + \
                        ((h2h["away_team"] == home_team) & (h2h["result"] == "A")).sum()
        h2h_away_wins = ((h2h["home_team"] == away_team) & (h2h["result"] == "H")).sum() + \
                        ((h2h["away_team"] == away_team) & (h2h["result"] == "A")).sum()
        h2h_draws = (h2h["result"] == "D").sum()

        hc1, hc2, hc3, hc4 = st.columns(4)
        with hc1:
            st.metric("Partidos", len(h2h))
        with hc2:
            st.metric(f"Victorias {home_team[:10]}", h2h_home_wins)
        with hc3:
            st.metric("Empates", h2h_draws)
        with hc4:
            st.metric(f"Victorias {away_team[:10]}", h2h_away_wins)

        for _, r in h2h.sort_values("date", ascending=False).iterrows():
            ht, at = r["home_team"], r["away_team"]
            hg, ag = r["home_goals"], r["away_goals"]
            date_str = r["date"].strftime("%d/%m/%Y") if pd.notna(r["date"]) else "—"
            result_color = "#22c55e" if (
                (ht == home_team and hg > ag) or (at == home_team and ag > hg)
            ) else ("#f59e0b" if hg == ag else "#ef4444")
            st.markdown(f"""
            <div class="score-row" style="margin-bottom:0.4rem;">
                <span style="color:#64748b;font-size:0.75rem;">{date_str}</span>
                <span class="score-name">{ht} <span style="color:{result_color};">{hg}–{ag}</span> {at}</span>
            </div>""", unsafe_allow_html=True)

    # ── FOOTER ─────────────────────────────────────────────────────────────
    # ── Footer con contador de visitas ────────────────────────────────────
    _visit_count = count_visit()
    st.markdown("---")
    st.caption(f"👁️ Visitas a la app: **{_visit_count:,}**  ·  Marca Zonal · Apertura 2026")
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;color:#334155;font-size:0.68rem;letter-spacing:1px;padding-top:1rem;
                border-top:1px solid rgba(14,165,233,0.1);margin-top:1rem;">
        MARCA ZONAL · Portal de Datos · Modelo estadístico basado en xG y distribución de Poisson<br/>
        Los porcentajes son estimaciones probabilísticas, no garantías de resultado.
    </div>""", unsafe_allow_html=True)

else:
    # Placeholder when no teams selected
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;color:#334155;">
        <div style="font-size:3rem;margin-bottom:1rem;">⚽</div>
        <div style="font-family:'Poppins',sans-serif;font-size:1.1rem;font-weight:600;color:#475569;">
            Seleccioná los dos equipos para ver las probabilidades
        </div>
        <div style="font-size:0.8rem;margin-top:0.5rem;color:#334155;letter-spacing:1px;">
            DIVISIÓN PROFESIONAL · PARAGUAY · 2026
        </div>
    </div>""", unsafe_allow_html=True)
