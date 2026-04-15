import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle


# Colors for the 4 metric categories
CATEGORY_COLORS = {
    'Defensa': '#166534',
    'Ataque': '#22c55e',
    'Posesion': '#4ade80',
    'Distribucion': '#84cc16',
}

SCOUT_CATEGORY_COLORS = {
    'Defensa': '#14b8a6',
    'Posesion': '#2563eb',
    'Ataque': '#be123c',
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
            percentile_value should be 0-100.

    Returns:
        matplotlib Figure
    """
    labels = []
    values = []
    colors = []

    spacing = 0.6

    for cat_name, metrics in reversed(categories_data):
        color = CATEGORY_COLORS.get(cat_name, '#888888')
        for metric_label, pct in reversed(metrics):
            labels.append(metric_label)
            values.append(pct)
            colors.append(color)
        labels.append(None)
        values.append(None)
        colors.append(None)

    if labels and labels[-1] is None:
        labels.pop()
        values.pop()
        colors.pop()

    y_positions = []
    current_y = 0
    for value in values:
        y_positions.append(current_y)
        current_y += spacing if value is None else 1

    fig_height = max(6, len([v for v in values if v is not None]) * 0.55 + 2.5)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    for y, label, value, color in zip(y_positions, labels, values, colors):
        if value is None:
            continue
        bar_obj = ax.barh(
            y, value, height=0.7, color=color,
            edgecolor='#000000', linewidth=0.5, zorder=3
        )[0]
        x_pos = bar_obj.get_width() + 1.5
        if x_pos > 95:
            x_pos = bar_obj.get_width() - 3
        ax.text(
            x_pos, bar_obj.get_y() + bar_obj.get_height() / 2,
            f'{value:.0f}', va='center', ha='left', fontsize=9,
            color='#F2F2F2', fontweight='bold', zorder=5
        )

    valid_ticks = [y for y, label in zip(y_positions, labels) if label is not None]
    valid_labels = [label for label in labels if label is not None]
    ax.set_yticks(valid_ticks)
    ax.set_yticklabels(valid_labels, fontsize=9, color='#F2F2F2')

    ax.set_xlim(0, 105)
    ax.set_xlabel('Percentil dentro del grupo de posicion', fontsize=11,
                  color='#F2F2F2', fontweight='bold')
    ax.set_xticks([0, 25, 50, 75, 100])

    for x in [25, 50, 75]:
        ax.axvline(x, color='white', linestyle=':', linewidth=0.5, alpha=0.3, zorder=1)

    ax.set_facecolor('#0f1117')
    fig.set_facecolor('#0f1117')
    ax.tick_params(colors='white', labelsize=9)
    ax.xaxis.label.set_color('white')
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['bottom', 'left']:
        ax.spines[spine].set_color('white')
        ax.spines[spine].set_linewidth(0.5)

    fig.text(0.515, 0.97, f"{player_name} | {player_team}",
             size=16, ha="center", fontweight='bold', color="#F2F2F2")
    fig.text(0.515, 0.945, subtitle,
             size=11, ha="center", color="#F2F2F2")

    legend_patches = [
        mpatches.Patch(color=CATEGORY_COLORS[cat], label=cat)
        for cat in CATEGORY_COLORS
    ]
    leg = ax.legend(handles=legend_patches, loc='lower right', fontsize=9,
                    framealpha=0.3, edgecolor='white', facecolor='#333333',
                    labelcolor='#F2F2F2')
    leg.get_frame().set_linewidth(0.5)

    fig.text(0.99, 0.01,
             "DATAVIZ DE MARCA ZONAL\nPercentiles relativos al grupo de posicion.",
             size=8, color="#F2F2F2", ha="right", fontstyle='italic')

    fig.subplots_adjust(left=0.32, top=0.92, bottom=0.08, right=0.95)
    return fig


def _format_scout_value(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}" if not float(value).is_integer() else f"{value:.0f}"
    return f"{value:.2f}".rstrip('0').rstrip('.')


def _draw_segmented_bar(ax, start_x, y, width, height, pct, fill_color, n_segments=10):
    gap = width * 0.012
    seg_w = (width - gap * (n_segments - 1)) / n_segments
    pct = float(np.clip(pct, 0, 100))
    filled = int(np.floor(pct / (100 / n_segments) + 1e-9))

    for idx in range(n_segments):
        x = start_x + idx * (seg_w + gap)
        face = fill_color if idx < filled else '#1f2937'
        edge = fill_color if idx < filled else '#243041'
        pill = FancyBboxPatch(
            (x, y - height / 2),
            seg_w,
            height,
            boxstyle=f"round,pad=0,rounding_size={height * 0.42}",
            linewidth=0.7,
            edgecolor=edge,
            facecolor=face,
            zorder=3,
        )
        ax.add_patch(pill)


def create_scout_report(player_name, player_team, subtitle, categories_data):
    """
    Create a compact scouting card inspired by segmented TV-style reports.

    categories_data:
      [
        ('Defensa', [{'label': 'Intercepciones', 'value': 12, 'pct': 78}, ...]),
        ('Posesion', [...]),
        ('Ataque', [...]),
      ]
    """
    n_groups = len(categories_data)
    total_rows = sum(len(items) for _, items in categories_data)
    fig_h = max(8.4, total_rows * 0.54 + n_groups * 0.72 + 2.2)
    fig, axes = plt.subplots(
        n_groups, 1, figsize=(8.4, fig_h),
        gridspec_kw={
            'height_ratios': [max(len(items), 1) + 0.85 for _, items in categories_data],
            'hspace': 0.10,
        },
    )
    if n_groups == 1:
        axes = [axes]

    fig.patch.set_facecolor('#050b14')

    for ax, (category_name, items) in zip(axes, categories_data):
        ax.set_facecolor('#08111d')
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.6, len(items) - 0.4)
        ax.invert_yaxis()
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        cat_color = SCOUT_CATEGORY_COLORS.get(category_name, '#22c55e')

        ax.add_patch(Rectangle((0, -1.0), 6.5, len(items) + 1.8, facecolor=cat_color, alpha=0.28, lw=0, zorder=0))
        ax.add_patch(Rectangle((6.2, -1.0), 0.45, len(items) + 1.8, facecolor=cat_color, alpha=0.9, lw=0, zorder=1))
        ax.text(
            3.25,
            (len(items) - 1) / 2 if items else 0,
            category_name.upper(),
            rotation=90,
            va='center',
            ha='center',
            fontsize=10.5,
            color=cat_color,
            fontweight='bold',
            alpha=0.95,
        )

        for row_idx, item in enumerate(items):
            value_txt = _format_scout_value(item.get('value', ''))
            label_txt = str(item.get('label', '')).upper()
            pct = float(item.get('pct', 0))

            ax.text(14.5, row_idx, value_txt, va='center', ha='right',
                    fontsize=12.2, color='#f8fafc', fontweight='bold')
            ax.text(16.6, row_idx, label_txt, va='center', ha='left',
                    fontsize=8.4, color='#cbd5e1', fontweight='bold')
            _draw_segmented_bar(ax, 38, row_idx, 57, 0.18, pct, cat_color)

        ax.axhline(len(items) - 0.42, color='#111827', linewidth=1.0, alpha=0.9)

    fig.text(0.5, 0.982, f"{player_name} | {player_team}", ha='center', va='top',
             fontsize=17, color='#f8fafc', fontweight='bold')
    fig.text(0.5, 0.956, subtitle, ha='center', va='top',
             fontsize=10.3, color='#94a3b8')
    fig.text(0.5, 0.02, "X: @marca_zonal  ·  Instagram: @marca.zonal",
             ha='center', va='bottom', fontsize=8.5, color='#6b7280', fontstyle='italic')

    fig.subplots_adjust(left=0.055, right=0.985, top=0.90, bottom=0.06)
    return fig
