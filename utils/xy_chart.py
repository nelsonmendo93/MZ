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
}
_DEFAULT_COLOR = '#22c55e'


def create_xy_chart(df, x_col, y_col, labeled_players=None,
                    x_label=None, y_label=None, logo_path=None,
                    liga_col='Liga'):
    """
    Scatter XY con puntos coloreados por liga.
    Solo muestra nombres para los jugadores en `labeled_players` (máx 5).

    Args:
        df: DataFrame con columnas Player, x_col, y_col y opcionalmente liga_col
        x_col / y_col: columnas de métricas
        labeled_players: lista de nombres a etiquetar (máx 5)
        liga_col: nombre de la columna de liga (default 'Liga')
    """
    labeled_players = [p for p in (labeled_players or []) if p]

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

    # Separar jugadores etiquetados del resto
    labeled_set = set(labeled_players)
    others = df[~df['Player'].isin(labeled_set)]
    labeled_df = df[df['Player'].isin(labeled_set)]

    # Plotear puntos del resto (sin nombre)
    if has_liga:
        for liga in ligas_presentes:
            grp = others[others[liga_col] == liga]
            if grp.empty:
                continue
            color = _LIGA_COLORS.get(liga, _DEFAULT_COLOR)
            ax.scatter(grp[x_col].astype(float), grp[y_col].astype(float),
                       c=color, alpha=0.55, s=70, zorder=5,
                       edgecolors='none')
        # También los sin liga conocida
        grp_none = others[~others[liga_col].isin(ligas_presentes)]
        if not grp_none.empty:
            ax.scatter(grp_none[x_col].astype(float), grp_none[y_col].astype(float),
                       c=_DEFAULT_COLOR, alpha=0.55, s=70, zorder=5, edgecolors='none')
    else:
        ax.scatter(others[x_col].astype(float), others[y_col].astype(float),
                   c=_DEFAULT_COLOR, alpha=0.55, s=70, zorder=5, edgecolors='none')

    # Plotear jugadores etiquetados (más grandes, borde blanco)
    texts = []
    for _, row in labeled_df.iterrows():
        xv, yv = float(row[x_col]), float(row[y_col])
        color = _point_color(row)
        ax.scatter(xv, yv, c=color, s=220, zorder=10,
                   edgecolors='white', linewidths=1.8)
        t = ax.text(xv, yv, row['Player'], fontsize=10, color='white',
                    ha='center', va='bottom', fontweight='bold', zorder=15)
        texts.append(t)

    # adjustText solo para etiquetados — params mínimos para compatibilidad cross-version
    if texts:
        try:
            adjust_text(
                texts, ax=ax,
                arrowprops=dict(color='gray', alpha=0.5, lw=0.6, shrinkA=4, shrinkB=4),
            )
        except Exception:
            pass  # si falla por versión, los textos se muestran sin ajuste de posición

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
        # labelcolor='white' requiere matplotlib>=3.3; fallback manual
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
