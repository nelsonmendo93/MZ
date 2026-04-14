import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os
from mplsoccer import PyPizza


# Colors for the 3 metric groups (5 metrics each)
GROUP_COLORS = ["#0ea5e9", "#f97316", "#a78bfa"]
GROUP_LABELS = ["Defensa", "Ataque", "Distribución"]


def _wrap_label(text, max_chars=15):
    """Inserta un salto de línea en el espacio más cercano al centro del texto.
    Busca en ambas direcciones y elige el más próximo al centro.
    Si el texto ya entra en max_chars, lo devuelve sin cambios."""
    if len(text) <= max_chars:
        return text
    mid = len(text) // 2
    left = right = -1
    for i in range(mid, 0, -1):
        if text[i] == ' ':
            left = i
            break
    for i in range(mid + 1, len(text)):
        if text[i] == ' ':
            right = i
            break
    if left == -1 and right == -1:
        return text
    if left == -1:
        best = right
    elif right == -1:
        best = left
    else:
        best = left if (mid - left) <= (right - mid) else right
    return text[:best] + '\n' + text[best + 1:]


def create_pizza_chart(player_name, player_team, subtitle, params, values,
                       min_range, max_range, center_image=None,
                       center_text="MARCA\nZONAL"):
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
    # Aplicar salto de línea a etiquetas largas
    params = [_wrap_label(p) for p in params]

    n_params = len(params)
    n_per_group = n_params // 3 if n_params >= 3 else n_params

    # Build color lists
    slice_colors = []
    text_colors = []
    for i, color in enumerate(GROUP_COLORS):
        count = n_per_group if i < 2 else (n_params - 2 * n_per_group)
        slice_colors.extend([color] * count)
        # All 3 group colors are dark/medium → white text
        text_colors.extend(["#F2F2F2"] * count)

    baker = PyPizza(
        params=params,
        min_range=min_range,
        max_range=max_range,
        background_color="#0f1117",
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
                      boxstyle="circle,pad=0.15", lw=1)
        ),
    )

    # Center: logo image if available, otherwise fallback to text
    if center_image and os.path.exists(center_image):
        logo = mpimg.imread(center_image)
        imagebox = OffsetImage(logo, zoom=0.05)
        ab = AnnotationBbox(imagebox, (-1.51, -14.5), frameon=False, zorder=20)
        ax.add_artist(ab)
    else:
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
             "DATAVIZ DE MARCA ZONAL\nMétricas per 90. Barras relativas al grupo de posición.\n"
             "𝕏: @marca_zonal  ·  Instagram: @marca.zonal",
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
