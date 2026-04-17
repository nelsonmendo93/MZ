import textwrap

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, FancyBboxPatch, Rectangle, Wedge


CATEGORY_COLORS = {
    'Defensa': '#166534',
    'Ataque': '#22c55e',
    'Posesion': '#4ade80',
    'Distribucion': '#84cc16',
}

LEAGUE_COLORS = {
    'PAR': '#dc2626',
    'ARG': '#14b8a6',
    'BRA': '#16a34a',
    'URU': '#2563eb',
    'COL': '#eab308',
    'ECU': '#7c3aed',
    'CHI': '#f97316',
}

SCOUT_PILL_COLORS = {
    'Ataque': '#e11d48',
    'Posesion': '#2563eb',
    'Pases': '#22c55e',
    'Defensa': '#14b8a6',
    'Creatividad': '#f59e0b',
}

SCOUT_PANEL_BG = '#08111d'
SCOUT_CARD_BG = '#0b1625'
SCOUT_BORDER = '#1f2937'
SCOUT_MUTED = '#94a3b8'


def create_bar_chart(player_name, player_team, subtitle, categories_data):
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


def _draw_segmented_bar(
    ax, start_x, y, width, height, pct, fill_color, n_segments=10, transform=None
):
    transform = transform or ax.transData
    gap = width * 0.012
    seg_w = (width - gap * (n_segments - 1)) / n_segments
    pct = float(np.clip(pct, 0, 100))
    filled = int(np.floor(pct / (100 / n_segments) + 1e-9))

    for idx in range(n_segments):
        x = start_x + idx * (seg_w + gap)
        face = fill_color if idx < filled else '#223047'
        edge = fill_color if idx < filled else '#223047'
        pill = FancyBboxPatch(
            (x, y - height / 2),
            seg_w,
            height,
            boxstyle=f"round,pad=0,rounding_size={height * 0.45}",
            linewidth=0.5,
            edgecolor=edge,
            facecolor=face,
            zorder=3,
            transform=transform,
        )
        ax.add_patch(pill)


def _truncate(text, max_len):
    text = str(text)
    return text if len(text) <= max_len else text[:max_len - 1] + '...'


def _draw_card(ax, x=0.0, y=0.0, w=1.0, h=1.0, radius=0.035, facecolor=SCOUT_PANEL_BG):
    ax.add_patch(FancyBboxPatch(
        (x + 0.01, y - 0.01), w, h,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        linewidth=0.0, edgecolor='none', facecolor='#030712',
        alpha=0.32, transform=ax.transAxes, zorder=0
    ))
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        linewidth=1.0, edgecolor=SCOUT_BORDER, facecolor=facecolor,
        transform=ax.transAxes, zorder=1
    ))


def _draw_gauge(ax, overall_score):
    ax.set_facecolor(SCOUT_PANEL_BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.0, 1.05)

    _draw_card(ax, radius=0.06)
    ax.text(0.08, 0.82, "MZ SCORE", transform=ax.transAxes, ha='left', va='top',
            fontsize=10.4, color='#38bdf8', fontweight='bold')

    base = Wedge((0, -0.10), 0.58, 0, 360, width=0.13, facecolor='#223047', edgecolor='none')
    fill = Wedge((0, -0.10), 0.58, 90, 90 + (360 * max(min(overall_score, 100), 0) / 100.0),
                 width=0.13, facecolor='#22c55e', edgecolor='none')
    ax.add_patch(base)
    ax.add_patch(fill)
    ax.text(0, -0.01, f"{overall_score:.0f}", ha='center', va='center',
            fontsize=33, color='#f8fafc', fontweight='bold')


def _draw_category_pill(ax, category_name, score):
    ax.set_facecolor(SCOUT_PANEL_BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    color = SCOUT_PILL_COLORS.get(category_name, '#64748b')
    _draw_card(ax, radius=0.05, facecolor=SCOUT_CARD_BG)
    ax.text(0.06, 0.69, category_name.upper(), transform=ax.transAxes,
            ha='left', va='center', fontsize=11.8, color=color, fontweight='bold')
    ax.text(0.93, 0.67, f"{float(np.clip(score, 0, 100)):.0f}", transform=ax.transAxes,
            ha='right', va='center', fontsize=13.0, color='#f8fafc', fontweight='bold')
    _draw_segmented_bar(ax, 0.06, 0.32, 0.88, 0.10, score, color, n_segments=12, transform=ax.transAxes)


def _draw_position_pitch(ax, position_label):
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_facecolor(SCOUT_PANEL_BG)

    pitch_bg = '#1c2435'
    line = '#d8dee9'
    thin = 0.8

    ax.add_patch(FancyBboxPatch(
        (0.04, 0.02), 0.92, 0.96,
        boxstyle="round,pad=0.01,rounding_size=0.025",
        linewidth=1.0, edgecolor=line, facecolor=pitch_bg,
        transform=ax.transAxes
    ))
    ax.add_patch(Rectangle((0.24, 0.84), 0.52, 0.14, linewidth=thin,
                           edgecolor=line, facecolor='none', transform=ax.transAxes))
    ax.add_patch(Rectangle((0.36, 0.91), 0.28, 0.07, linewidth=thin,
                           edgecolor=line, facecolor='none', transform=ax.transAxes))
    ax.add_patch(Rectangle((0.24, 0.02), 0.52, 0.14, linewidth=thin,
                           edgecolor=line, facecolor='none', transform=ax.transAxes))
    ax.add_patch(Rectangle((0.36, 0.02), 0.28, 0.07, linewidth=thin,
                           edgecolor=line, facecolor='none', transform=ax.transAxes))
    ax.plot([0.04, 0.96], [0.50, 0.50], color=line, lw=thin, transform=ax.transAxes)
    ax.add_patch(plt.Circle((0.50, 0.50), 0.115, edgecolor=line,
                            facecolor='none', lw=thin, transform=ax.transAxes))
    ax.add_patch(plt.Circle((0.50, 0.50), 0.008, edgecolor='none', facecolor=line, transform=ax.transAxes))
    ax.add_patch(plt.Circle((0.50, 0.18), 0.008, edgecolor='none', facecolor=line, transform=ax.transAxes))
    ax.add_patch(plt.Circle((0.50, 0.82), 0.008, edgecolor='none', facecolor=line, transform=ax.transAxes))

    position_map = {
        'GK': (0.50, 0.09), 'CB': (0.50, 0.21), 'LCB': (0.34, 0.25), 'RCB': (0.66, 0.25),
        'LB': (0.18, 0.24), 'RB': (0.82, 0.24), 'WB': (0.82, 0.33), 'LWB': (0.18, 0.33),
        'RWB': (0.82, 0.33), 'DMF': (0.50, 0.34), 'CMF': (0.50, 0.50), 'AMF': (0.50, 0.65),
        'LCMF': (0.36, 0.50), 'RCMF': (0.64, 0.50), 'LAMF': (0.34, 0.65), 'RAMF': (0.66, 0.65),
        'LW': (0.20, 0.74), 'RW': (0.80, 0.74), 'LWF': (0.20, 0.74), 'RWF': (0.80, 0.74),
        'CF': (0.50, 0.85), 'ST': (0.50, 0.85), 'SS': (0.50, 0.74),
    }
    clean_label = str(position_label or '').strip().upper()
    x, y = position_map.get(clean_label, (0.50, 0.52))
    bbox = ax.get_position()
    aspect_ratio = bbox.height / bbox.width if bbox.width else 1.0
    marker_h = 0.156
    marker_w = marker_h * aspect_ratio
    ax.add_patch(Ellipse((x, y), marker_w, marker_h, facecolor='#38bdf8',
                         edgecolor='white', lw=0.8, transform=ax.transAxes))
    ax.text(x, y, clean_label[:4] if clean_label else '--', transform=ax.transAxes,
            ha='center', va='center', fontsize=5.0, color='white', fontweight='bold')


def _draw_summary_box(ax, title, rows, player_position, title_color='#f8fafc'):
    ax.set_facecolor(SCOUT_PANEL_BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    _draw_card(ax, radius=0.04)
    ax.text(0.06, 0.93, title.upper(), transform=ax.transAxes,
            ha='left', va='top', fontsize=9.3, color=title_color, fontweight='bold')

    ax.add_patch(FancyBboxPatch(
        (0.62, 0.18), 0.28, 0.56,
        boxstyle="round,pad=0.01,rounding_size=0.025",
        linewidth=0.8, edgecolor=SCOUT_BORDER, facecolor=SCOUT_CARD_BG,
        transform=ax.transAxes
    ))
    ax.text(0.76, 0.68, "POSICION", transform=ax.transAxes,
            ha='center', va='top', fontsize=5.8, color='#64748b', fontweight='bold')
    pitch_ax = ax.inset_axes([0.695, 0.225, 0.13, 0.42])
    _draw_position_pitch(pitch_ax, player_position)

    left_x = 0.06
    box_w = 0.24
    box_h = 0.16
    positions = [
        (left_x, 0.58),
        (left_x + 0.27, 0.58),
        (left_x, 0.37),
        (left_x + 0.27, 0.37),
        (left_x, 0.16),
    ]

    for idx, (label, value) in enumerate(rows[:5]):
        x, y = positions[idx]
        w = 0.51 if idx == 4 else box_w
        ax.add_patch(FancyBboxPatch(
            (x, y), w, box_h,
            boxstyle="round,pad=0.01,rounding_size=0.025",
            linewidth=0.8, edgecolor=SCOUT_BORDER, facecolor=SCOUT_CARD_BG,
            transform=ax.transAxes
        ))
        ax.text(x + 0.03, y + box_h - 0.035, str(label).upper(), transform=ax.transAxes,
                ha='left', va='top', fontsize=5.8, color='#64748b', fontweight='bold')
        ax.text(x + 0.03, y + 0.055, _truncate(value, 24 if idx == 4 else 12), transform=ax.transAxes,
                ha='left', va='bottom', fontsize=9.2, color='#f8fafc', fontweight='bold')


def _draw_info_box(ax, title, rows, title_color='#f8fafc'):
    ax.set_facecolor(SCOUT_PANEL_BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    _draw_card(ax, radius=0.04)
    ax.text(0.06, 0.93, title.upper(), transform=ax.transAxes,
            ha='left', va='top', fontsize=9.3, color=title_color, fontweight='bold')

    if not rows:
        ax.text(0.06, 0.78, "Sin datos disponibles.", transform=ax.transAxes,
                ha='left', va='top', fontsize=7.8, color=SCOUT_MUTED)
        return

    y = 0.82

    for row in rows:
        kind = row.get('kind', 'label_value')
        if kind == 'label_value':
            ax.text(0.06, y, row['label'].upper(), transform=ax.transAxes,
                    ha='left', va='top', fontsize=5.9, color='#6b7280', fontweight='bold')
            ax.text(0.06, y - 0.055, _truncate(row['value'], 24), transform=ax.transAxes,
                    ha='left', va='top', fontsize=8.9, color='#f8fafc', fontweight='bold')
            y -= 0.125
        elif kind == 'metric_rank':
            metric_label = str(row['metric'])
            metric_fontsize = 6.8
            if len(metric_label) > 40:
                metric_fontsize = 6.1
            if len(metric_label) > 55:
                metric_fontsize = 5.6
            wrapped = "\n".join(textwrap.wrap(metric_label, width=42)) if len(metric_label) > 42 else metric_label
            is_multiline = "\n" in wrapped
            row_height = 0.142 if is_multiline else 0.112
            ax.add_patch(FancyBboxPatch(
                (0.05, y - row_height), 0.90, row_height,
                boxstyle="round,pad=0.01,rounding_size=0.02",
                linewidth=0.8, edgecolor=SCOUT_BORDER, facecolor=SCOUT_CARD_BG,
                transform=ax.transAxes
            ))
            ax.add_patch(Rectangle((0.055, y - row_height + 0.01), 0.008, row_height - 0.02,
                                   transform=ax.transAxes, facecolor='#22c55e', edgecolor='none'))
            ax.text(0.08, y - 0.020, wrapped, transform=ax.transAxes,
                    ha='left', va='top', fontsize=metric_fontsize, color='#e2e8f0',
                    fontweight='bold', linespacing=1.0)
            value_y = y - (0.092 if is_multiline else 0.075)
            rank_y = y - (0.066 if is_multiline else 0.052)
            ax.text(0.08, value_y, _format_scout_value(row['value']), transform=ax.transAxes,
                    ha='left', va='center', fontsize=7.5, color='#cbd5e1', fontweight='bold')
            ax.text(0.92, rank_y, f"{row['rank']}°/{row['pool_size']}", transform=ax.transAxes,
                    ha='right', va='center', fontsize=7.1, color='#22c55e', fontweight='bold')
            y -= row_height + 0.034
        elif kind == 'similar':
            badge_color = row.get('color', '#64748b')
            ax.add_patch(FancyBboxPatch(
                (0.05, y - 0.108), 0.90, 0.108,
                boxstyle="round,pad=0.01,rounding_size=0.02",
                linewidth=0.8, edgecolor=SCOUT_BORDER, facecolor=SCOUT_CARD_BG,
                transform=ax.transAxes
            ))
            ax.text(0.08, y - 0.026, _truncate(row['player'], 22), transform=ax.transAxes,
                    ha='left', va='center', fontsize=7.2, color='#f8fafc', fontweight='bold')
            ax.text(0.08, y - 0.072, _truncate(row['team'], 20), transform=ax.transAxes,
                    ha='left', va='center', fontsize=6.4, color='#94a3b8')
            age_value = row.get('age', '--')
            ax.add_patch(FancyBboxPatch(
                (0.49, y - 0.085), 0.09, 0.034,
                boxstyle="round,pad=0.006,rounding_size=0.014",
                linewidth=0.0, edgecolor='none', facecolor='#0f1c2e',
                transform=ax.transAxes
            ))
            ax.text(0.535, y - 0.068, f"{age_value}", transform=ax.transAxes,
                    ha='center', va='center', fontsize=6.2, color='#cbd5e1', fontweight='bold')
            ax.add_patch(FancyBboxPatch(
                (0.60, y - 0.085), 0.09, 0.034,
                boxstyle="round,pad=0.008,rounding_size=0.015",
                linewidth=0.0, edgecolor='none', facecolor=badge_color,
                transform=ax.transAxes
            ))
            ax.text(0.645, y - 0.068, row['league'], transform=ax.transAxes,
                    ha='center', va='center', fontsize=6.1, color='#ffffff', fontweight='bold')
            ax.text(0.92, y - 0.052, f"{row['similarity']:.1f}%", transform=ax.transAxes,
                    ha='right', va='center', fontsize=6.9, color='#f8fafc', fontweight='bold')
            y -= 0.146


def create_scout_report(
    player_name,
    player_team,
    subtitle,
    categories_data,
    summary_items=None,
    top_metrics=None,
    similars_data=None,
    overall_score=0.0,
    category_scores=None,
    player_position='',
):
    summary_items = summary_items or []
    top_metrics = top_metrics or []
    similars_data = similars_data or []
    category_scores = category_scores or []

    fig = plt.figure(figsize=(9.1, 10.5), facecolor='#050b14')
    gs = fig.add_gridspec(
        18, 12, left=0.04, right=0.985, top=0.90, bottom=0.06,
        wspace=0.16, hspace=0.18
    )

    left_gs = gs[:, 0:5].subgridspec(18, 1, hspace=0.15)
    right_gs = gs[:, 5:12].subgridspec(18, 7, hspace=0.16, wspace=0.12)

    gauge_ax = fig.add_subplot(left_gs[0:6, 0])
    _draw_gauge(gauge_ax, overall_score)

    desired_order = ['CRE', 'ATQ', 'PAS', 'DEF', 'POS']
    score_lookup = {item.get('code', ''): item for item in category_scores}
    ordered_scores = [score_lookup[code] for code in desired_order if code in score_lookup]
    ordered_scores.extend([item for item in category_scores if item.get('code', '') not in desired_order])
    row_slices = [(6, 8), (8, 10), (10, 12), (12, 14), (14, 16)]

    for idx, item in enumerate(ordered_scores[:5]):
        r1, r2 = row_slices[idx]
        cat_ax = fig.add_subplot(left_gs[r1:r2, 0])
        _draw_category_pill(cat_ax, item.get('label', item.get('code', '')), item.get('score', 0))

    top_metric_rows = [
        {
            'kind': 'metric_rank',
            'metric': item['metric'],
            'value': item['value'],
            'rank': item['rank'],
            'pool_size': item['pool_size'],
        }
        for item in top_metrics[:5]
    ]
    similar_rows = [
        {
            'kind': 'similar',
            'player': item['player'],
            'team': item['team'],
            'age': item.get('age', '--'),
            'league': item['league'],
            'similarity': item['similarity'],
            'color': LEAGUE_COLORS.get(item['league'], '#64748b'),
        }
        for item in similars_data[:5]
    ]

    summary_ax = fig.add_subplot(right_gs[0:6, 0:7])
    _draw_summary_box(summary_ax, 'Resumen del jugador', summary_items, player_position, title_color='#38bdf8')

    top_metrics_ax = fig.add_subplot(right_gs[6:12, 0:7])
    _draw_info_box(top_metrics_ax, 'Top 5 metricas', top_metric_rows, title_color='#22c55e')

    similars_ax = fig.add_subplot(right_gs[12:18, 0:7])
    _draw_info_box(similars_ax, 'Top 5 similares', similar_rows, title_color='#f59e0b')

    fig.text(0.05, 0.965, "VISTA SCOUT", ha='left', va='top',
             fontsize=9.5, color='#14b8a6', fontweight='bold')
    fig.text(0.05, 0.94, player_name.upper(), ha='left', va='top',
             fontsize=18.2, color='#f8fafc', fontweight='bold')
    fig.text(0.05, 0.915, f"{player_team} | {subtitle}", ha='left', va='top',
             fontsize=8.7, color='#94a3b8')
    fig.text(0.98, 0.02, "X: @marca_zonal | Instagram: @marca.zonal",
             ha='right', va='bottom', fontsize=8.0, color='#6b7280', fontstyle='italic')

    return fig
