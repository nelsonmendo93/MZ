import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from adjustText import adjust_text

# Colores por liga (mismo esquema que el resto de la app)
_LIGA_COLORS = {
    'PAR': '#dc2626',
    'ARG': '#75caed',
    'BRA': '#16a34a',
    'URU': '#2563eb',
    'COL': '#eab308',
    'ECU': '#7c3aed',
    'CHI': '#f97316',
    'PER': '#e879f9',
    'VEN': '#2dd4bf',
    'ALE': '#facc15',
    'ESP': '#f43f5e',
    'FRA': '#60a5fa',
    'ING': '#a78bfa',
    'ITA': '#34d399',
}
_DEFAULT_COLOR = '#22c55e'


def _select_auto_labels(df, x_col, y_col, forced_set, min_dist=0.06):
    """
    Greedy: elige qué jugadores pueden tener etiqueta automática sin encimarse.
    Usa distancia euclídea normalizada entre puntos.
    Los de forced_set se incluyen siempre y reservan su espacio.

    Args:
        min_dist: distancia mínima entre puntos para coexistir (fracción del rango)
    Returns:
        set de nombres de jugadores con etiqueta auto (NO incluye forced_set)
    """
    x_data = df[x_col].astype(float).values
    y_data = df[y_col].astype(float).values
    players = df['Player'].values

    x_range = x_data.max() - x_data.min() or 1.0
    y_range = y_data.max() - y_data.min() or 1.0

    x_norm = (x_data - x_data.min()) / x_range
    y_norm = (y_data - y_data.min()) / y_range

    # índices de forced primero para reservar espacio
    occupied = []
    for i, player in enumerate(players):
        if player in forced_set:
            occupied.append((x_norm[i], y_norm[i]))

    auto_labeled = set()
    for i, player in enumerate(players):
        if player in forced_set:
            continue
        xi, yi = x_norm[i], y_norm[i]
        too_close = any(
            ((xi - xj) ** 2 + (yi - yj) ** 2) ** 0.5 < min_dist
            for xj, yj in occupied
        )
        if not too_close:
            auto_labeled.add(player)
            occupied.append((xi, yi))

    return auto_labeled


def create_xy_chart(df, x_col, y_col, labeled_players=None,
                    x_label=None, y_label=None, logo_path=None,
                    liga_col='Liga'):
    """
    Scatter XY con puntos coloreados por liga.

    Etiquetado en dos capas:
    - AUTO: todos los jugadores cuyo punto no se encima con otro → font pequeño, alpha moderado
    - FORZADO (labeled_players): siempre muestran nombre → font grande, bold, punto destacado

    Args:
        df: DataFrame con columnas Player, x_col, y_col y opcionalmente liga_col
        x_col / y_col: columnas de métricas
        labeled_players: lista de nombres a forzar etiqueta (máx 5)
        liga_col: nombre de la columna de liga (default 'Liga')
    """
    labeled_players = [p for p in (labeled_players or []) if p]
    forced_set = set(labeled_players)

    if x_label is None:
        x_label = x_col
    if y_label is None:
        y_label = y_col

    fig, ax = plt.subplots(figsize=(13, 10))

    x_data = df[x_col].astype(float)
    y_data = df[y_col].astype(float)
    x_mean = x_data.mean()
    y_mean = y_data.mean()

    x_min, x_max = x_data.min(), x_data.max()
    y_min, y_max = y_data.min(), y_data.max()
    x_pad = (x_max - x_min) * 0.10
    y_pad = (y_max - y_min) * 0.10

    # Líneas de cuadrante
    ax.axvline(x_mean, color='white', linestyle='--', linewidth=1.2, alpha=0.5, zorder=3)
    ax.axhline(y_mean, color='white', linestyle='--', linewidth=1.2, alpha=0.5, zorder=3)
    ax.text(x_max + x_pad * 0.4, y_mean, 'Promedio', fontsize=9, color='white',
            ha='left', va='center', alpha=0.5, fontstyle='italic', zorder=4)
    ax.text(x_mean, y_max + y_pad * 0.4, 'Promedio', fontsize=9, color='white',
            ha='center', va='bottom', alpha=0.5, fontstyle='italic', zorder=4)

    # Determinar color de cada punto según liga
    has_liga = liga_col in df.columns
    ligas_presentes = sorted(df[liga_col].dropna().unique()) if has_liga else []

    def _point_color(row):
        if not has_liga:
            return _DEFAULT_COLOR
        return _LIGA_COLORS.get(str(row.get(liga_col, '')), _DEFAULT_COLOR)

    # Calcular qué jugadores tienen etiqueta auto (sin encimarse)
    auto_set = _select_auto_labels(df, x_col, y_col, forced_set, min_dist=0.06)

    # Separar en 3 grupos: forzados, auto, sin etiqueta
    df_forced = df[df['Player'].isin(forced_set)]
    df_auto = df[df['Player'].isin(auto_set)]
    df_plain = df[~df['Player'].isin(forced_set | auto_set)]

    # ---- Plotear puntos sin etiqueta ----
    def _scatter_group(grp_df, alpha=0.50, size=65):
        if grp_df.empty:
            return
        if has_liga:
            for liga in ligas_presentes:
                grp = grp_df[grp_df[liga_col] == liga]
                if grp.empty:
                    continue
                color = _LIGA_COLORS.get(liga, _DEFAULT_COLOR)
                ax.scatter(grp[x_col].astype(float), grp[y_col].astype(float),
                           c=color, alpha=alpha, s=size, zorder=5, edgecolors='none')
            grp_none = grp_df[~grp_df[liga_col].isin(ligas_presentes)]
            if not grp_none.empty:
                ax.scatter(grp_none[x_col].astype(float), grp_none[y_col].astype(float),
                           c=_DEFAULT_COLOR, alpha=alpha, s=size, zorder=5, edgecolors='none')
        else:
            ax.scatter(grp_df[x_col].astype(float), grp_df[y_col].astype(float),
                       c=_DEFAULT_COLOR, alpha=alpha, s=size, zorder=5, edgecolors='none')

    _scatter_group(df_plain, alpha=0.50, size=65)

    # ---- Etiquetas automáticas (fondo semi-transparente, font pequeño) ----
    texts_auto = []
    for _, row in df_auto.iterrows():
        xv, yv = float(row[x_col]), float(row[y_col])
        color = _point_color(row)
        ax.scatter(xv, yv, c=color, alpha=0.65, s=65, zorder=6, edgecolors='none')
        t = ax.text(
            xv, yv, row['Player'],
            fontsize=7.5, color='white', alpha=0.75,
            ha='center', va='bottom', zorder=11,
            bbox=dict(boxstyle='round,pad=0.15', facecolor='#0f1117',
                      alpha=0.35, edgecolor='none'),
        )
        texts_auto.append(t)

    # ---- Etiquetas forzadas (siempre visibles, bold) ----
    texts_forced = []
    for _, row in df_forced.iterrows():
        xv, yv = float(row[x_col]), float(row[y_col])
        color = _point_color(row)
        ax.scatter(xv, yv, c=color, s=230, zorder=12,
                   edgecolors='white', linewidths=1.8)
        t = ax.text(
            xv, yv, row['Player'],
            fontsize=10, color='white', fontweight='bold',
            ha='center', va='bottom', zorder=16,
        )
        texts_forced.append(t)

    # ---- adjustText separado por capa ----
    if texts_auto:
        try:
            adjust_text(
                texts_auto, ax=ax,
                arrowprops=dict(color='gray', alpha=0.35, lw=0.5,
                                shrinkA=3, shrinkB=3),
            )
        except Exception:
            pass

    if texts_forced:
        try:
            adjust_text(
                texts_forced, ax=ax,
                arrowprops=dict(color='gray', alpha=0.55, lw=0.7,
                                shrinkA=4, shrinkB=4),
            )
        except Exception:
            pass

    # Leyenda de ligas (solo las presentes en el gráfico)
    if has_liga and ligas_presentes:
        legend_handles = [
            mpatches.Patch(color=_LIGA_COLORS.get(lg, _DEFAULT_COLOR), label=lg)
            for lg in ligas_presentes
        ]
        leg = ax.legend(
            handles=legend_handles,
            loc='lower right',
            fontsize=9,
            framealpha=0.25,
            facecolor='#0f1117',
            edgecolor='#2d3748',
            ncol=min(4, len(ligas_presentes)),
            handlelength=1.2,
            handleheight=1.0,
        )
        for txt in leg.get_texts():
            txt.set_color('white')

    # Estilos de ejes
    ax.set_xlabel(x_label, color='white', fontsize=13, fontweight='bold')
    ax.set_ylabel(y_label, color='white', fontsize=13, fontweight='bold')
    ax.set_title(f'{y_label} vs {x_label}', color='white', fontsize=15, fontweight='bold', pad=14)

    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    ax.grid(True, linestyle=':', alpha=0.25, color='white')
    ax.set_facecolor('#0f1117')
    fig.set_facecolor('#0f1117')
    ax.tick_params(colors='white', labelsize=9)
    for spine in ax.spines.values():
        spine.set_color('#2d3748')
        spine.set_linewidth(0.8)

    fig.text(0.5, 0.003, '𝕏: @marca_zonal  ·  Instagram: @marca.zonal',
             size=9, color='#aaaaaa', ha='center', va='bottom', fontstyle='italic')

    fig.tight_layout()
    return fig
