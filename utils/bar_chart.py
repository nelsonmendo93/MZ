import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# Colors for the 4 metric categories
CATEGORY_COLORS = {
    'Defensa': '#2a6f97',
    'Ataque': '#e63946',
    'Posesión': '#588b8b',
    'Distribución': '#f4a261',
}


def create_bar_chart(player_name, player_team, subtitle, categories_data):
    """
    Create a horizontal grouped bar chart showing player percentiles.

    Args:
        player_name: Player name for the title
        player_team: Team name for the title
        subtitle: Subtitle text (e.g. "Entre 41 delanteros | Apertura 2026")
        categories_data: OrderedDict or list of tuples:
            [(category_name, [(metric_label, percentile_value), ...]), ...]
            percentile_value should be 0–100.

    Returns:
        matplotlib Figure
    """
    # Flatten data: build labels and values in reverse order (top-to-bottom)
    labels = []
    values = []
    colors = []
    category_positions = []  # (y_position, category_name) for headers

    y = 0
    spacing = 0.6  # gap before each category header

    for cat_name, metrics in reversed(categories_data):
        color = CATEGORY_COLORS.get(cat_name, '#888888')
        # Add metrics (reversed so first metric is at top within group)
        for metric_label, pct in reversed(metrics):
            labels.append(metric_label)
            values.append(pct)
            colors.append(color)
            y += 1
        # Record category header position (centered on its metrics)
        mid = y - len(metrics) / 2
        category_positions.append((mid, cat_name, color))
        y += spacing  # gap between categories

    n_bars = len(labels)
    y_positions = []
    current_y = 0
    bar_idx = 0
    for cat_name, metrics in reversed(categories_data):
        for _ in metrics:
            y_positions.append(current_y)
            current_y += 1
            bar_idx += 1
        current_y += spacing

    # Figure
    fig_height = max(6, n_bars * 0.55 + 2.5)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    bar_height = 0.7
    bars = ax.barh(y_positions, values, height=bar_height, color=colors,
                   edgecolor='#000000', linewidth=0.5, zorder=3)

    # Value labels on each bar
    for bar_obj, val in zip(bars, values):
        x_pos = bar_obj.get_width() + 1.5
        if x_pos > 95:
            x_pos = bar_obj.get_width() - 3
        ax.text(x_pos, bar_obj.get_y() + bar_obj.get_height() / 2,
                f'{val:.0f}', va='center', ha='left', fontsize=9,
                color='#F2F2F2', fontweight='bold', zorder=5)

    # Metric labels on y-axis
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=9, color='#F2F2F2')


    # X-axis
    ax.set_xlim(0, 105)
    ax.set_xlabel('Percentil dentro del grupo de posición', fontsize=11,
                  color='#F2F2F2', fontweight='bold')
    ax.set_xticks([0, 25, 50, 75, 100])

    # Reference lines
    for x in [25, 50, 75]:
        ax.axvline(x, color='white', linestyle=':', linewidth=0.5, alpha=0.3, zorder=1)

    # Styling
    ax.set_facecolor('#222222')
    fig.set_facecolor('#222222')
    ax.tick_params(colors='white', labelsize=9)
    ax.xaxis.label.set_color('white')
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['bottom', 'left']:
        ax.spines[spine].set_color('white')
        ax.spines[spine].set_linewidth(0.5)

    # Title & subtitle
    fig.text(0.515, 0.97, f"{player_name} | {player_team}",
             size=16, ha="center", fontweight='bold', color="#F2F2F2")
    fig.text(0.515, 0.945, subtitle,
             size=11, ha="center", color="#F2F2F2")

    # Legend
    legend_patches = [
        mpatches.Patch(color=CATEGORY_COLORS[cat], label=cat)
        for cat in CATEGORY_COLORS
    ]
    leg = ax.legend(handles=legend_patches, loc='lower right', fontsize=9,
                    framealpha=0.3, edgecolor='white', facecolor='#333333',
                    labelcolor='#F2F2F2')
    leg.get_frame().set_linewidth(0.5)

    # Branding
    fig.text(0.99, 0.01,
             "DATAVIZ DE MARCA ZONAL\nPercentiles relativos al grupo de posición.",
             size=8, color="#F2F2F2", ha="right", fontstyle='italic')

    fig.subplots_adjust(left=0.32, top=0.92, bottom=0.08, right=0.95)
    return fig
