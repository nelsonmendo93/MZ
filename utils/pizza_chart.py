import matplotlib.pyplot as plt
from mplsoccer import PyPizza


# Colors for the 3 metric groups (5 metrics each)
GROUP_COLORS = ["#2a6f97", "#588b8b", "#8d0801"]
GROUP_LABELS = ["Defensa", "Ataque", "Distribución"]


def create_pizza_chart(player_name, player_team, subtitle, params, values,
                       min_range, max_range, center_text="MARCA\nZONAL"):
    """
    Create a PyPizza radar chart for a player.

    Args:
        player_name: Player name for the title
        player_team: Team name for the title
        subtitle: Subtitle text (e.g. "Entre 41 delanteros +1000 min | LPF 2025")
        params: List of metric names (should be 15, in groups of 5)
        values: List of metric values for the player
        min_range: List of min values (from position group)
        max_range: List of max values (from position group)
        center_text: Text to display in the center instead of a photo

    Returns:
        matplotlib Figure
    """
    n_params = len(params)
    n_per_group = n_params // 3 if n_params >= 3 else n_params

    # Build color lists
    slice_colors = []
    text_colors = []
    for i, color in enumerate(GROUP_COLORS):
        count = n_per_group if i < 2 else (n_params - 2 * n_per_group)
        slice_colors.extend([color] * count)
        # Light text on dark slices, dark text on lighter slices
        if i < 2:
            text_colors.extend(["#000000"] * count)
        else:
            text_colors.extend(["#F2F2F2"] * count)

    baker = PyPizza(
        params=params,
        min_range=min_range,
        max_range=max_range,
        background_color="#222222",
        straight_line_color="#000000",
        straight_line_lw=1,
        last_circle_color="#000000",
        last_circle_lw=1,
        other_circle_lw=1,
        inner_circle_size=15,
    )

    fig, ax = baker.make_pizza(
        values,
        figsize=(9, 9.5),
        color_blank_space="same",
        slice_colors=slice_colors,
        value_colors=text_colors,
        value_bck_colors=slice_colors,
        blank_alpha=0.4,
        kwargs_slices=dict(edgecolor="#000000", zorder=2, linewidth=1),
        kwargs_params=dict(color="#F2F2F2", fontsize=8, va="center"),
        kwargs_values=dict(
            color="#F2F2F2", fontsize=9, zorder=3,
            bbox=dict(edgecolor="#000000", facecolor="cornflowerblue",
                      boxstyle="circle,pad=0.2", lw=1)
        ),
    )

    # Center text instead of image — small enough to fit inside inner circle
    ax.text(0, 0, center_text, ha='center', va='center',
            fontsize=9, fontweight='bold', color='#F2F2F2',
            zorder=20)

    # Title
    fig.text(0.515, 0.975, f"{player_name} | {player_team}",
             size=16, ha="center", fontweight='bold', color="#F2F2F2")

    # Subtitle
    fig.text(0.515, 0.955, subtitle,
             size=12, ha="center", color="#F2F2F2")

    # Credits
    fig.text(0.99, 0.02,
             "DATAVIZ DE MARCA ZONAL\nMétricas per 90. Barras relativas\nal grupo de posición.",
             size=9, color="#F2F2F2", ha="right", fontstyle='italic')

    # Category legend: dots well spaced from their labels
    legend_items = list(zip(GROUP_COLORS, GROUP_LABELS))
    x_start = 0.28
    x_spacing = 0.20
    for i, (color, label) in enumerate(legend_items):
        dot_x = x_start + i * x_spacing
        fig.patches.append(
            plt.Circle((dot_x, 0.932), 0.012, fill=True, color=color,
                        transform=fig.transFigure, zorder=20)
        )
        fig.text(dot_x + 0.025, 0.928, label,
                 size=11, fontweight='bold', color="#F2F2F2")

    return fig
