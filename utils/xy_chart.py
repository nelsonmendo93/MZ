import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text


def create_xy_chart(df, x_col, y_col, highlight_player=None,
                    x_label=None, y_label=None):
    """
    Create an XY scatter chart with quadrant divisions.

    Args:
        df: DataFrame with player data (must contain 'Player' column and x_col, y_col)
        x_col: Column name for X axis
        y_col: Column name for Y axis
        highlight_player: Player name to highlight (larger dot, different color)
        x_label: Display label for X axis (defaults to x_col)
        y_label: Display label for Y axis (defaults to y_col)

    Returns:
        matplotlib Figure
    """
    if x_label is None:
        x_label = x_col
    if y_label is None:
        y_label = y_col
    fig, ax = plt.subplots(figsize=(12, 10))

    x_data = df[x_col].astype(float)
    y_data = df[y_col].astype(float)
    x_mean = x_data.mean()
    y_mean = y_data.mean()

    # Draw quadrant dividing lines
    ax.axvline(x_mean, color='white', linestyle='--', linewidth=1.5, alpha=0.7, zorder=3)
    ax.axhline(y_mean, color='white', linestyle='--', linewidth=1.5, alpha=0.7, zorder=3)

    x_min, x_max = x_data.min(), x_data.max()
    y_min, y_max = y_data.min(), y_data.max()
    x_pad = (x_max - x_min) * 0.08
    y_pad = (y_max - y_min) * 0.08

    # "Promedio" labels on the dashed lines
    ax.text(x_max + x_pad * 0.5, y_mean, 'Promedio', fontsize=10, color='white',
            ha='left', va='center', alpha=0.7, fontstyle='italic', zorder=4)
    ax.text(x_mean, y_max + y_pad * 0.5, 'Promedio', fontsize=10, color='white',
            ha='center', va='bottom', alpha=0.7, fontstyle='italic', zorder=4)

    # Separate highlighted player from the rest
    if highlight_player and highlight_player in df['Player'].values:
        others = df[df['Player'] != highlight_player]
        player_row = df[df['Player'] == highlight_player].iloc[0]
    else:
        others = df
        player_row = None

    # Plot all other players
    ax.scatter(others[x_col].astype(float), others[y_col].astype(float),
               c='#6a994e', alpha=0.6, s=120, zorder=5, edgecolors='white', linewidths=0.5)

    # Plot highlighted player
    if player_row is not None:
        ax.scatter(float(player_row[x_col]), float(player_row[y_col]),
                   c='#e63946', s=250, zorder=10, edgecolors='white', linewidths=2,
                   label=highlight_player)

    # Add text labels with adjustText to avoid overlapping
    texts = []
    for _, row in df.iterrows():
        x, y = float(row[x_col]), float(row[y_col])
        name = row['Player']
        weight = 'bold' if name == highlight_player else 'normal'
        color = '#e63946' if name == highlight_player else 'white'
        fontsize = 11 if name == highlight_player else 9
        t = ax.text(x, y, name, fontsize=fontsize, color=color, ha='center', va='bottom',
                    fontweight=weight, zorder=15)
        texts.append(t)

    # Adjust text positions to avoid overlap
    adjust_text(texts, ax=ax,
                arrowprops=dict(color='gray', alpha=0.4,
                                lw=0.5, shrinkA=5, shrinkB=5),
                expand=(1.5, 1.5),
                force_text=(0.8, 0.8),
                force_points=(0.5, 0.5),
                only_move={'text': 'xy'})

    # Axis styling
    ax.set_xlabel(x_label, color='white', fontsize=14, fontweight='bold')
    ax.set_ylabel(y_label, color='white', fontsize=14, fontweight='bold')
    title = f'{y_label} vs {x_label}'
    if highlight_player:
        title += f' | {highlight_player}'
    ax.set_title(title, color='white', fontsize=16, fontweight='bold', pad=15)

    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    ax.grid(True, linestyle=':', alpha=0.3, color='white')
    ax.set_facecolor('#222222')
    fig.set_facecolor('#222222')
    ax.tick_params(colors='white', labelsize=9)
    for spine in ax.spines.values():
        spine.set_color('white')
        spine.set_linewidth(1)

    # Branding credit (same style as radar chart)
    fig.text(0.99, 0.02,
             "DATAVIZ DE MARCA ZONAL\nMétricas per 90.",
             size=9, color="#F2F2F2", ha="right", fontstyle='italic')

    fig.tight_layout()
    return fig
