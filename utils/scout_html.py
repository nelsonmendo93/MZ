import base64
import html
import os


def _load_domtoimage_js():
    js_path = os.path.join(os.path.dirname(__file__), 'dom-to-image-more.min.js')
    if not os.path.exists(js_path):
        return ''
    with open(js_path, 'r', encoding='utf-8') as f:
        return f.read()


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


def _esc(value):
    return html.escape(str(value))


def _format_value(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}" if not float(value).is_integer() else f"{value:.0f}"
    return f"{value:.2f}".rstrip('0').rstrip('.')


def _load_logo_data_uri():
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'logo_blanco.png')
    if not os.path.exists(logo_path):
        return ''
    with open(logo_path, 'rb') as fh:
        encoded = base64.b64encode(fh.read()).decode('ascii')
    return f"data:image/png;base64,{encoded}"


def _render_segments(score, color, n=12):
    filled = max(0, min(n, round((float(score) / 100) * n)))
    pills = []
    for idx in range(n):
        bg = color if idx < filled else '#223047'
        pills.append(f'<span class="mz-pill" style="background:{bg};"></span>')
    return ''.join(pills)


def _position_marker(position_label):
    mapping = {
        'GK': ('50%', '90%'), 'CB': ('50%', '78%'), 'LCB': ('36%', '78%'), 'RCB': ('64%', '78%'),
        'LB': ('20%', '75%'), 'RB': ('80%', '75%'), 'WB': ('80%', '67%'), 'LWB': ('20%', '67%'),
        'RWB': ('80%', '67%'), 'DMF': ('50%', '64%'), 'CMF': ('50%', '50%'), 'AMF': ('50%', '35%'),
        'LCMF': ('38%', '50%'), 'RCMF': ('62%', '50%'), 'LAMF': ('35%', '35%'), 'RAMF': ('65%', '35%'),
        'LW': ('22%', '25%'), 'RW': ('78%', '25%'), 'LWF': ('22%', '25%'), 'RWF': ('78%', '25%'),
        'CF': ('50%', '16%'), 'ST': ('50%', '16%'), 'SS': ('50%', '26%'),
    }
    clean = str(position_label or '').strip().upper()
    left, top = mapping.get(clean, ('50%', '50%'))
    return clean[:4] if clean else '--', left, top


def _render_pitch(position_label):
    label, left, top = _position_marker(position_label)
    return f"""
    <div class="mz-pos-card">
      <div class="mz-meta-label">POSICION</div>
      <div class="mz-pitch">
        <div class="mz-pitch-box mz-pitch-box-top"></div>
        <div class="mz-pitch-box mz-pitch-goal-top"></div>
        <div class="mz-pitch-box mz-pitch-box-bottom"></div>
        <div class="mz-pitch-box mz-pitch-goal-bottom"></div>
        <div class="mz-pitch-midline"></div>
        <div class="mz-pitch-circle"></div>
        <div class="mz-pitch-dot mz-pitch-dot-top"></div>
        <div class="mz-pitch-dot mz-pitch-dot-mid"></div>
        <div class="mz-pitch-dot mz-pitch-dot-bottom"></div>
        <div class="mz-position-marker" style="left:{left}; top:{top};">{_esc(label)}</div>
      </div>
    </div>
    """


def build_scout_html(
    player_name,
    player_team,
    subtitle,
    summary_items=None,
    top_metrics=None,
    similars_data=None,
    overall_score=0.0,
    category_scores=None,
    player_position='',
    pentagon_img_b64=None,
):
    summary_items = summary_items or []
    top_metrics = top_metrics or []
    similars_data = similars_data or []
    category_scores = category_scores or []
    logo_uri = _load_logo_data_uri()

    summary_cards = []
    for idx, (label, value) in enumerate(summary_items[:6]):
        summary_cards.append(
            f"""
            <div class="mz-summary-card">
              <div class="mz-meta-label">{_esc(label).upper()}</div>
              <div class="mz-meta-value">{_esc(value)}</div>
            </div>
            """
        )

    desired_order = ['CRE', 'ATQ', 'PAS', 'DEF', 'POS']
    lookup = {item.get('code', ''): item for item in category_scores}
    ordered = [lookup[code] for code in desired_order if code in lookup]
    ordered.extend([item for item in category_scores if item.get('code', '') not in desired_order])
    pill_cards = []
    for item in ordered[:5]:
        label = item.get('label', item.get('code', ''))
        score = float(item.get('score', 0))
        color = SCOUT_PILL_COLORS.get(label, '#64748b')
        pill_cards.append(
            f"""
            <div class="mz-axis-card">
              <div class="mz-axis-top">
                <span class="mz-axis-label" style="color:{color};">{_esc(label).upper()}</span>
                <span class="mz-axis-score">{score:.0f}</span>
              </div>
              <div class="mz-pill-row">{_render_segments(score, color)}</div>
            </div>
            """
        )

    metric_cards = []
    for item in top_metrics[:5]:
        metric_cards.append(
            f"""
            <div class="mz-list-card mz-list-card-metric">
              <div class="mz-list-accent"></div>
              <div class="mz-list-main">
                <div class="mz-list-title">{_esc(item.get('metric', ''))}</div>
                <div class="mz-list-sub">{_esc(_format_value(item.get('value', '')))}</div>
              </div>
              <div class="mz-list-right mz-list-rank">{int(item.get('rank', 0))}º/{int(item.get('pool_size', 0))}</div>
            </div>
            """
        )

    similar_cards = []
    for item in similars_data[:5]:
        league = str(item.get('league', ''))
        badge = LEAGUE_COLORS.get(league, '#64748b')
        similar_cards.append(
            f"""
            <div class="mz-list-card mz-list-card-similar">
              <div class="mz-sim-grid">
                <div class="mz-sim-col">
                  <div class="mz-sim-player">{_esc(item.get('player', ''))}</div>
                </div>
                <div class="mz-sim-col">
                  <span class="mz-age-chip">{_esc(item.get('age', '--'))}</span>
                </div>
                <div class="mz-sim-col">
                  <div class="mz-sim-team">{_esc(item.get('team', ''))}</div>
                </div>
                <div class="mz-sim-col">
                  <span class="mz-league-chip" style="background:{badge};">{_esc(league)}</span>
                </div>
                <div class="mz-sim-col mz-sim-score">{float(item.get('similarity', 0)):.1f}%</div>
              </div>
            </div>
            """
        )

    score = max(0, min(100, float(overall_score)))
    return f"""
    <style>
      /* ── Base (desktop / export) ─────────────────────────────────── */
      .mz-root {{
        background:#050b14;
        color:#f8fafc;
        font-family:'Cousine','DejaVu Sans Mono',monospace;
        padding:13px 13px 9px 13px;
      }}
      .mz-label-top {{
        color:#14b8a6;
        font-weight:800;
        font-size:13px;
        margin-bottom:7px;
      }}
      .mz-player {{
        font-size:36px;
        font-weight:900;
        line-height:1;
        margin-bottom:6px;
      }}
      .mz-subtitle {{
        color:#94a3b8;
        font-size:12px;
        margin-bottom:10px;
      }}
      .mz-grid {{
        display:grid;
        grid-template-columns:1.05fr 1.45fr;
        gap:9px;
      }}
      .mz-left, .mz-right {{
        display:flex;
        flex-direction:column;
        gap:9px;
      }}
      .mz-logo-space {{
        flex:1;
        min-height:44px;
        display:flex;
        align-items:center;
        justify-content:center;
      }}
      .mz-footer-bar {{
        display:flex;
        align-items:center;
        justify-content:flex-end;
        width:100%;
        margin-top:8px;
        padding:0 2px;
      }}
      .mz-footer-social {{
        color:#6b7280;
        font-size:11px;
        text-align:right;
        line-height:1.4;
      }}
      .mz-card {{
        background:{SCOUT_PANEL_BG};
        border:1px solid {SCOUT_BORDER};
        border-radius:14px;
        box-shadow:0 6px 16px rgba(0,0,0,.18);
      }}
      .mz-score-card {{
        padding:16px 18px 14px;
      }}
      .mz-score-title {{
        color:#38bdf8;
        font-weight:900;
        font-size:17px;
        margin-bottom:8px;
        line-height:1.05;
        text-align:center;
      }}
      .mz-score-wrap {{
        display:flex;
        justify-content:center;
        align-items:center;
      }}
      .mz-score-ring {{
        width:180px;
        height:180px;
        border-radius:50%;
        background:conic-gradient(from 0deg, #22c55e 0deg, #22c55e {score*3.6}deg, #223047 {score*3.6}deg, #223047 360deg);
        display:flex;
        align-items:center;
        justify-content:center;
      }}
      .mz-score-hole {{
        width:114px;
        height:114px;
        border-radius:50%;
        background:#08111d;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:42px;
        font-weight:900;
      }}
      .mz-axis-card {{
        padding:10px 13px;
        background:{SCOUT_CARD_BG};
        border:1px solid {SCOUT_BORDER};
        border-radius:12px;
      }}
      .mz-axis-top {{
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:7px;
      }}
      .mz-axis-label {{
        font-size:15px;
        font-weight:900;
      }}
      .mz-axis-score {{
        font-size:16px;
        font-weight:900;
      }}
      .mz-pill-row {{
        display:grid;
        grid-template-columns:repeat(12,1fr);
        gap:4px;
      }}
      .mz-pill {{
        height:10px;
        border-radius:999px;
      }}
      .mz-panel {{
        padding:12px 14px 10px;
      }}
      .mz-panel-title {{
        font-size:13px;
        font-weight:900;
        margin-bottom:9px;
      }}
      .mz-panel-title-summary {{
        font-size:14px;
      }}
      .mz-panel-title.blue {{ color:#38bdf8; }}
      .mz-panel-title.green {{ color:#22c55e; }}
      .mz-panel-title.orange {{ color:#f59e0b; }}
      .mz-summary-layout {{
        display:grid;
        grid-template-columns:1.1fr .65fr;
        gap:10px;
        align-items:stretch;
      }}
      .mz-summary-grid {{
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:8px;
      }}
      .mz-summary-card {{
        background:{SCOUT_CARD_BG};
        border:1px solid {SCOUT_BORDER};
        border-radius:11px;
        padding:10px 12px;
        min-height:52px;
      }}
      .mz-summary-card-wide {{
        grid-column:1 / span 2;
      }}
      .mz-meta-label {{
        font-size:10px;
        color:#64748b;
        font-weight:800;
        margin-bottom:4px;
        letter-spacing:.04em;
      }}
      .mz-meta-value {{
        font-size:17px;
        font-weight:900;
      }}
      .mz-pos-card {{
        background:{SCOUT_CARD_BG};
        border:1px solid {SCOUT_BORDER};
        border-radius:11px;
        padding:10px 8px 8px;
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:flex-start;
      }}
      .mz-pitch {{
        position:relative;
        width:90px;
        height:180px;
        margin-top:6px;
        background:#1c2435;
        border:2px solid #d8dee9;
        border-radius:5px;
      }}
      .mz-pitch-box {{
        position:absolute;
        left:50%;
        transform:translateX(-50%);
        border:2px solid #d8dee9;
      }}
      .mz-pitch-box-top {{ top:0; width:54px; height:25px; border-top:0; }}
      .mz-pitch-goal-top {{ top:0; width:30px; height:13px; border-top:0; }}
      .mz-pitch-box-bottom {{ bottom:0; width:54px; height:25px; border-bottom:0; }}
      .mz-pitch-goal-bottom {{ bottom:0; width:30px; height:13px; border-bottom:0; }}
      .mz-pitch-midline {{
        position:absolute; left:0; right:0; top:50%;
        border-top:2px solid #d8dee9;
      }}
      .mz-pitch-circle {{
        position:absolute; left:50%; top:50%;
        width:30px; height:30px; transform:translate(-50%,-50%);
        border:2px solid #d8dee9; border-radius:50%;
      }}
      .mz-pitch-dot {{
        position:absolute; left:50%; width:3px; height:3px; transform:translateX(-50%);
        background:#d8dee9; border-radius:50%;
      }}
      .mz-pitch-dot-top {{ top:22%; }}
      .mz-pitch-dot-mid {{ top:50%; margin-top:-1px; }}
      .mz-pitch-dot-bottom {{ bottom:22%; }}
      .mz-position-marker {{
        position:absolute;
        width:22px; height:22px;
        transform:translate(-50%,-50%);
        border-radius:50%;
        background:#38bdf8;
        border:2px solid #ffffff;
        color:#ffffff;
        font-size:8px;
        font-weight:900;
        display:flex;
        align-items:center;
        justify-content:center;
      }}
      .mz-list-card {{
        background:{SCOUT_CARD_BG};
        border:1px solid {SCOUT_BORDER};
        border-radius:11px;
        padding:8px 12px;
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:10px;
      }}
      .mz-list-card + .mz-list-card {{ margin-top:6px; }}
      .mz-list-card-metric {{
        position:relative;
        padding-left:14px;
      }}
      .mz-list-accent {{
        position:absolute;
        left:0;
        top:8px;
        bottom:8px;
        width:5px;
        border-radius:999px;
        background:#22c55e;
      }}
      .mz-list-main {{
        flex:1;
        min-width:0;
      }}
      .mz-list-title {{
        font-size:11px;
        font-weight:800;
        line-height:1.25;
        white-space:normal;
        word-break:break-word;
      }}
      .mz-list-sub {{
        font-size:10px;
        color:#cbd5e1;
        font-weight:700;
        margin-top:3px;
      }}
      .mz-list-right {{
        flex:none;
        font-size:11px;
        font-weight:900;
      }}
      .mz-list-rank {{ color:#22c55e; }}
      .mz-sim-grid {{
        width:100%;
        display:grid;
        grid-template-columns:minmax(0,2fr) 32px minmax(0,1.3fr) 40px 50px;
        gap:6px;
        align-items:center;
      }}
      .mz-sim-col {{ min-width:0; }}
      .mz-sim-player {{
        font-size:12px;
        font-weight:900;
        color:#f8fafc;
        line-height:1.15;
        white-space:normal;
        word-break:break-word;
      }}
      .mz-sim-team {{
        font-size:11px;
        color:#cbd5e1;
        font-weight:700;
        line-height:1.15;
        white-space:normal;
        word-break:break-word;
      }}
      .mz-age-chip, .mz-league-chip {{
        height:20px;
        border-radius:7px;
        display:inline-flex;
        align-items:center;
        justify-content:center;
        font-size:10px;
        font-weight:800;
      }}
      .mz-age-chip {{ background:#0f1c2e; color:#cbd5e1; width:100%; }}
      .mz-league-chip {{ color:#fff; width:100%; }}
      .mz-sim-score {{
        min-width:0;
        text-align:right;
        font-size:11px;
        font-weight:900;
      }}
      .mz-footer {{ display:none; }}

      /* ── Mobile: layout apilado — activado via JS (.mz-mobile) ─────── */
      /* Se usa clase JS en vez de @media para poder exportar en desktop  */
      .mz-mobile {{ padding:10px 10px 8px !important; }}
      .mz-mobile .mz-player {{ font-size:22px !important; margin-bottom:4px !important; }}
      .mz-mobile .mz-label-top {{ font-size:11px !important; margin-bottom:5px !important; }}
      .mz-mobile .mz-subtitle {{ font-size:10px !important; margin-bottom:8px !important; }}

      .mz-mobile .mz-grid {{ grid-template-columns:1fr !important; gap:8px !important; }}

      .mz-mobile .mz-left {{
        display:grid !important;
        grid-template-columns:auto 1fr !important;
        gap:7px !important;
        align-items:start !important;
      }}
      .mz-mobile .mz-card.mz-score-card {{
        grid-column:1 !important;
        grid-row:1 / span 6 !important;
        padding:10px 12px !important;
        align-self:start !important;
      }}
      .mz-mobile .mz-score-title {{ font-size:10px !important; margin-bottom:6px !important; }}
      .mz-mobile .mz-score-ring {{ width:110px !important; height:110px !important; }}
      .mz-mobile .mz-score-hole {{ width:70px !important; height:70px !important; font-size:26px !important; }}

      .mz-mobile .mz-axis-card {{
        grid-column:2 !important;
        padding:6px 10px !important;
        border-radius:9px !important;
      }}
      .mz-mobile .mz-axis-top {{ margin-bottom:4px !important; }}
      .mz-mobile .mz-axis-label {{ font-size:12px !important; }}
      .mz-mobile .mz-axis-score {{ font-size:13px !important; }}
      .mz-mobile .mz-pill {{ height:7px !important; }}
      .mz-mobile .mz-pill-row {{ gap:3px !important; }}

      .mz-mobile .mz-logo-space {{
        grid-column:1 / span 2 !important;
        min-height:30px !important;
      }}

      .mz-mobile .mz-right {{ gap:7px !important; }}
      .mz-mobile .mz-panel {{ padding:9px 11px 8px !important; }}
      .mz-mobile .mz-panel-title {{ font-size:11px !important; margin-bottom:7px !important; }}

      .mz-mobile .mz-summary-layout {{ grid-template-columns:1fr !important; gap:6px !important; }}
      .mz-mobile .mz-pos-card {{ display:none !important; }}
      .mz-mobile .mz-summary-grid {{ grid-template-columns:repeat(3,1fr) !important; gap:6px !important; }}
      .mz-mobile .mz-summary-card {{ padding:7px 9px !important; min-height:42px !important; border-radius:9px !important; }}
      .mz-mobile .mz-meta-label {{ font-size:9px !important; margin-bottom:2px !important; }}
      .mz-mobile .mz-meta-value {{ font-size:13px !important; }}

      .mz-mobile .mz-list-card {{ padding:6px 10px !important; gap:8px !important; border-radius:9px !important; }}
      .mz-mobile .mz-list-card + .mz-list-card {{ margin-top:5px !important; }}
      .mz-mobile .mz-list-title {{ font-size:10px !important; }}
      .mz-mobile .mz-list-sub {{ font-size:9px !important; }}
      .mz-mobile .mz-list-right {{ font-size:10px !important; }}
      .mz-mobile .mz-sim-player {{ font-size:10px !important; }}
      .mz-mobile .mz-sim-team {{ font-size:9px !important; }}

      .mz-mobile .mz-footer-bar {{ margin-top:6px !important; }}
      .mz-mobile .mz-footer-social {{ font-size:9px !important; }}
    </style>
    <div class="mz-root">
      <div class="mz-label-top">VISTA SCOUT</div>
      <div class="mz-player">{_esc(player_name).upper()}</div>
      <div class="mz-subtitle">{_esc(player_team)} | {_esc(subtitle)}</div>
      <div class="mz-grid">
        <div class="mz-left">
          {'<div class="mz-card mz-score-card" style="padding:10px 12px;"><div class="mz-score-title" style="text-align:center;margin-bottom:6px;">MARCA ZONAL SCORE</div><img src="data:image/png;base64,' + pentagon_img_b64 + '" style="width:100%;border-radius:6px;display:block;" /></div>' if pentagon_img_b64 else '<div class="mz-card mz-score-card"><div class="mz-score-title" style="text-align:center;">MARCA ZONAL SCORE</div><div class="mz-score-wrap"><div class="mz-score-ring"><div class="mz-score-hole">' + f'{score:.0f}' + '</div></div></div></div>' + ''.join(pill_cards)}
          <div class="mz-logo-space">
            <canvas id="mz-logo-canvas" width="320" height="120" style="opacity:.92;filter:drop-shadow(0 2px 10px rgba(0,0,0,.4));max-width:100%;"></canvas>
          </div>
        </div>
        <div class="mz-right">
          <div class="mz-card mz-panel">
            <div class="mz-panel-title mz-panel-title-summary blue">RESUMEN DEL JUGADOR</div>
            <div class="mz-summary-layout">
              <div class="mz-summary-grid">
                {''.join(summary_cards)}
              </div>
              {_render_pitch(player_position)}
            </div>
          </div>
          <div class="mz-card mz-panel">
            <div class="mz-panel-title green">TOP 5 METRICAS</div>
            {''.join(metric_cards)}
          </div>
          <div class="mz-card mz-panel">
            <div class="mz-panel-title orange">TOP 5 SIMILARES</div>
            {''.join(similar_cards)}
          </div>
        </div>
      </div>
      <div class="mz-footer-bar">
        <div class="mz-footer-social">X: @marca_zonal &nbsp;·&nbsp; Instagram: @marca.zonal</div>
      </div>
    </div>

    <div style="text-align:center; margin-top:14px; padding-bottom:10px;">
      <button id="mz-dl-btn" onclick="mzGenerate()" style="
        background:#22c55e;
        color:#050b14;
        border:none;
        border-radius:10px;
        padding:12px 32px;
        font-size:15px;
        font-weight:900;
        font-family:'Cousine','DejaVu Sans Mono',monospace;
        cursor:pointer;
        letter-spacing:.04em;
      ">⬇ GENERAR PNG</button>
      <div id="mz-dl-status" style="color:#64748b;font-size:12px;font-family:monospace;margin-top:8px;min-height:16px;"></div>
      <div id="mz-preview-wrap" style="display:none; margin-top:14px;">
        <div style="color:#94a3b8;font-size:12px;font-family:monospace;margin-bottom:8px;">
          Desktop: click derecho → Guardar imagen &nbsp;|&nbsp; Móvil: mantené presionado → Guardar
        </div>
        <img id="mz-preview-img" style="max-width:100%;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.4);" />
      </div>
    </div>

    <script>
    {_load_domtoimage_js()}
    </script>
    <script>
    var MZ_LOGO_URI = '{logo_uri if logo_uri else ""}';

    function mzDrawLogo(canvas) {{
      if (!MZ_LOGO_URI) return Promise.resolve();
      return new Promise(function(resolve) {{
        var img = new Image();
        img.onload = function() {{
          var ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          resolve();
        }};
        img.onerror = function() {{ resolve(); }};
        img.src = MZ_LOGO_URI;
      }});
    }}

    // Dibuja el logo al cargar la página + aplica layout móvil si corresponde
    function mzApplyResponsive() {{
      var root = document.querySelector('.mz-root');
      if (!root) return;
      if (window.innerWidth <= 540) {{
        root.classList.add('mz-mobile');
      }} else {{
        root.classList.remove('mz-mobile');
      }}
    }}
    document.addEventListener('DOMContentLoaded', function() {{
      var c = document.getElementById('mz-logo-canvas');
      if (c) mzDrawLogo(c);
      mzApplyResponsive();
    }});
    window.addEventListener('resize', mzApplyResponsive);

    function mzGenerate() {{
      var btn    = document.getElementById('mz-dl-btn');
      var status = document.getElementById('mz-dl-status');
      var wrap   = document.getElementById('mz-preview-wrap');
      var img    = document.getElementById('mz-preview-img');

      btn.disabled    = true;
      btn.textContent = 'Generando...';
      status.textContent = '';

      var logoCanvas = document.getElementById('mz-logo-canvas');
      var node       = document.querySelector('.mz-root');
      var scale      = 2;

      // Quitar layout móvil para capturar siempre en desktop
      var wasMobile = node.classList.contains('mz-mobile');
      node.classList.remove('mz-mobile');

      mzDrawLogo(logoCanvas).then(function() {{
        return domtoimage.toPng(node, {{
          width:  node.scrollWidth  * scale,
          height: node.scrollHeight * scale,
          style: {{
            transform: 'scale(' + scale + ')',
            transformOrigin: 'top left',
            width:  node.scrollWidth  + 'px',
            height: node.scrollHeight + 'px',
          }},
          bgcolor: '#050b14',
        }});
      }})
      .then(function(dataUrl) {{
        img.src = dataUrl;
        wrap.style.display = 'block';
        btn.disabled    = false;
        btn.textContent = '⬇ GENERAR PNG';
        status.textContent = '✓ Imagen lista — guardala con click derecho (desktop) o mantené presionado (móvil)';
        // Restaurar layout móvil si estaba activo
        if (wasMobile) node.classList.add('mz-mobile');
        try {{
          var a = document.createElement('a');
          a.href     = dataUrl;
          a.download = '{_esc(player_name).replace(" ", "_")}_scout.png';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        }} catch(e) {{}}
      }})
      .catch(function(err) {{
        if (wasMobile) node.classList.add('mz-mobile');
        btn.disabled    = false;
        btn.textContent = '⬇ GENERAR PNG';
        status.textContent = 'Error: ' + String(err);
      }});
    }}
    </script>
    """

