"""report.svg_primitives · SVG 图元 + 颜色常量 · v3.2 从 assemble_report.py 抽离.

19 个 svg_* 函数 · 独立无业务依赖 · 全部是纯渲染.

### 颜色语义
- COLOR_BULL · 看多绿 #059669
- COLOR_BEAR · 看空红 #dc2626
- COLOR_GOLD · 金色（高亮 / gauge）#d97706
- COLOR_CYAN · 青（主要数据色）#0891b2
- COLOR_BLUE / COLOR_PINK / COLOR_INDIGO · 辅助
- COLOR_MUTED · 灰 #94a3b8
- COLOR_GRID · 浅灰 #e2e8f0

### 函数清单
- svg_sparkline / svg_h_bar_compare / svg_donut / svg_gauge / svg_radar
- svg_signal_lights / svg_supply_flow / svg_timeline / svg_bars
- svg_candlestick / svg_pe_band / svg_progress_row / svg_peer_table
- svg_unlock_timeline / svg_dividend_combo / svg_institutional_quarters / svg_thermometer

### 向后兼容
assemble_report.py 保留 `from lib.report.svg_primitives import *` · 所有旧调用工作.
"""
from __future__ import annotations


COLOR_BULL = "#059669"
COLOR_BEAR = "#dc2626"
COLOR_GOLD = "#d97706"
COLOR_CYAN = "#0891b2"
COLOR_BLUE = "#2563eb"
COLOR_PINK = "#db2777"
COLOR_INDIGO = "#4f46e5"
COLOR_MUTED = "#94a3b8"
COLOR_GRID = "#e2e8f0"


def svg_sparkline(values: list, width: int = 240, height: int = 50, color: str = COLOR_CYAN, fill: bool = True) -> str:
    """Tiny line chart. Values normalized to fit."""
    if not values or len(values) < 2:
        return f'<svg width="{width}" height="{height}"></svg>'
    vmin, vmax = min(values), max(values)
    span = max(vmax - vmin, 1e-9)
    pts = []
    for i, v in enumerate(values):
        x = i / (len(values) - 1) * (width - 4) + 2
        y = height - 4 - (v - vmin) / span * (height - 8)
        pts.append(f"{x:.1f},{y:.1f}")
    path = "M " + " L ".join(pts)
    fill_path = ""
    if fill:
        fill_path = f'<path d="{path} L {width-2},{height-2} L 2,{height-2} Z" fill="{color}" fill-opacity="0.12"/>'
    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block">
  {fill_path}
  <path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="{pts[-1].split(',')[0]}" cy="{pts[-1].split(',')[1]}" r="3" fill="{color}"/>
</svg>'''


def svg_h_bar_compare(label_a: str, val_a: float, label_b: str, val_b: float, unit: str = "", width: int = 260) -> str:
    """Horizontal back-to-back bar comparing two values."""
    max_v = max(abs(val_a), abs(val_b), 1)
    pct_a = abs(val_a) / max_v * 100
    pct_b = abs(val_b) / max_v * 100
    color_a = COLOR_BULL if val_a >= val_b else COLOR_MUTED
    color_b = COLOR_BULL if val_b > val_a else COLOR_MUTED
    return f'''<div style="font-family: Fira Code, monospace; font-size: 11px;">
  <div style="display:flex; justify-content:space-between; margin-bottom:4px; color:#475569;">
    <span>{label_a}</span><strong style="color:#0f172a">{val_a}{unit}</strong>
  </div>
  <div style="height:8px; background:#f1f5f9; border-radius:4px; overflow:hidden; margin-bottom:8px;">
    <div style="width:{pct_a}%; height:100%; background:{color_a}; border-radius:4px;"></div>
  </div>
  <div style="display:flex; justify-content:space-between; margin-bottom:4px; color:#475569;">
    <span>{label_b}</span><strong style="color:#0f172a">{val_b}{unit}</strong>
  </div>
  <div style="height:8px; background:#f1f5f9; border-radius:4px; overflow:hidden;">
    <div style="width:{pct_b}%; height:100%; background:{color_b}; border-radius:4px;"></div>
  </div>
</div>'''


def svg_donut(segments: list[tuple], total: float = None, label: str = "", size: int = 120) -> str:
    """Donut chart. segments = [(label, value, color), ...]"""
    if not segments:
        return ""
    total = total or sum(s[1] for s in segments)
    if total <= 0:
        return ""
    cx = cy = size / 2
    r = size / 2 - 8
    inner_r = r * 0.6
    paths = []
    cur_angle = -90  # start at top
    import math
    for lbl, val, color in segments:
        sweep = val / total * 360
        if sweep <= 0:
            continue
        end_angle = cur_angle + sweep
        large = 1 if sweep > 180 else 0
        x1 = cx + r * math.cos(math.radians(cur_angle))
        y1 = cy + r * math.sin(math.radians(cur_angle))
        x2 = cx + r * math.cos(math.radians(end_angle))
        y2 = cy + r * math.sin(math.radians(end_angle))
        x3 = cx + inner_r * math.cos(math.radians(end_angle))
        y3 = cy + inner_r * math.sin(math.radians(end_angle))
        x4 = cx + inner_r * math.cos(math.radians(cur_angle))
        y4 = cy + inner_r * math.sin(math.radians(cur_angle))
        d = f"M {x1},{y1} A {r},{r} 0 {large} 1 {x2},{y2} L {x3},{y3} A {inner_r},{inner_r} 0 {large} 0 {x4},{y4} Z"
        paths.append(f'<path d="{d}" fill="{color}"/>')
        cur_angle = end_angle
    legend = "".join(
        f'<div style="display:flex; align-items:center; gap:6px; font-size:10px; margin-bottom:2px;">'
        f'<span style="width:8px; height:8px; background:{c}; border-radius:2px"></span>'
        f'<span style="color:#475569">{l}</span>'
        f'<strong style="margin-left:auto; color:#0f172a">{v}</strong></div>'
        for l, v, c in segments
    )
    return f'''<div style="display:flex; align-items:center; gap:14px;">
  <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="flex-shrink:0">
    {"".join(paths)}
    {f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-family="Fira Sans" font-weight="700" font-size="14" fill="#0f172a">{label}</text>' if label else ""}
  </svg>
  <div style="flex:1; min-width:0">{legend}</div>
</div>'''


def svg_gauge(value: float, max_val: float = 100, label: str = "", size: int = 220, color: str = COLOR_GOLD, unit: str = "") -> str:
    """Semi-circle gauge — larger, bolder."""
    pct = max(0, min(1, value / max_val))
    cx = size / 2
    cy = size * 0.65
    r = size * 0.40
    import math
    val_a = 180 - pct * 180
    bg = f'<path d="M {cx-r},{cy} A {r},{r} 0 0 1 {cx+r},{cy}" fill="none" stroke="#e2e8f0" stroke-width="14" stroke-linecap="round"/>'
    x2 = cx + r * math.cos(math.radians(val_a))
    y2 = cy + r * math.sin(math.radians(val_a))
    large = 1 if pct > 0.5 else 0
    val_arc = f'<path d="M {cx-r},{cy} A {r},{r} 0 {large} 1 {x2},{y2}" fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round"/>'
    return f'''<svg width="{size}" height="{size*0.78}" viewBox="0 0 {size} {size*0.78}">
  {bg}
  {val_arc}
  <text x="{cx}" y="{cy-4}" text-anchor="middle" font-family="Fira Sans" font-weight="900" font-size="52" fill="#0f172a" letter-spacing="-2">{value:.0f}<tspan font-size="20" fill="#64748b" dx="2">{unit}</tspan></text>
  <text x="{cx}" y="{cy+22}" text-anchor="middle" font-family="Fira Sans" font-size="12" font-weight="600" fill="#475569">{label}</text>
</svg>'''


def svg_radar(labels: list, values: list, max_val: float = 10, size: int = 160) -> str:
    """5-axis radar chart."""
    import math
    n = len(labels)
    cx = cy = size / 2
    r = size * 0.38
    # axis lines + labels
    axes = []
    for i, lbl in enumerate(labels):
        a = -math.pi / 2 + i * 2 * math.pi / n
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        axes.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#e2e8f0" stroke-width="1"/>')
        lx = cx + (r + 12) * math.cos(a)
        ly = cy + (r + 14) * math.sin(a)
        axes.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-family="Fira Code" font-size="9" fill="#64748b">{lbl}</text>')
    # rings
    for ring in (0.33, 0.66, 1.0):
        ring_r = r * ring
        axes.append(f'<circle cx="{cx}" cy="{cy}" r="{ring_r}" fill="none" stroke="#f1f5f9"/>')
    # value polygon
    pts = []
    for i, v in enumerate(values):
        a = -math.pi / 2 + i * 2 * math.pi / n
        rv = r * (v / max_val)
        x = cx + rv * math.cos(a)
        y = cy + rv * math.sin(a)
        pts.append(f"{x:.1f},{y:.1f}")
    poly = f'<polygon points="{" ".join(pts)}" fill="{COLOR_CYAN}" fill-opacity="0.25" stroke="{COLOR_CYAN}" stroke-width="2"/>'
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{"".join(axes)}{poly}</svg>'


def svg_signal_lights(hit: int, total: int = 8) -> str:
    """N LED dots, hit ones red, ok ones green."""
    cells = []
    for i in range(total):
        on = i < hit
        color = COLOR_BEAR if on else COLOR_BULL
        opacity = 1 if on else 0.35
        cells.append(
            f'<div style="width:24px;height:24px;border-radius:50%;background:{color};opacity:{opacity};'
            f'box-shadow:0 0 8px {color}40;display:flex;align-items:center;justify-content:center;'
            f'color:#fff;font-family:Fira Code;font-size:10px;font-weight:700">{i+1}</div>'
        )
    label = "🔴 命中信号" if hit > 0 else "🟢 全部通过"
    return f'''<div>
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">{"".join(cells)}</div>
  <div style="font-family:Fira Code;font-size:10px;color:#475569">{label} · {hit}/{total}</div>
</div>'''


def svg_supply_flow(upstream: str, company: str, downstream: str) -> str:
    """Visual upstream → company → downstream flow. Truncate long text to prevent overflow."""
    # Truncate each segment to prevent CSS overflow
    def _trunc(s: str, max_len: int = 60) -> str:
        s = str(s).strip()
        if len(s) > max_len:
            return s[:max_len] + "…"
        return s
    upstream = _trunc(upstream, 50)
    company = _trunc(company, 30)
    downstream = _trunc(downstream, 50)

    return f'''<div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:8px;align-items:center;font-family:Fira Sans;overflow:hidden">
  <div style="padding:10px 12px;background:#cffafe;border:1px solid #0891b2;border-radius:8px;text-align:center;overflow:hidden">
    <div style="font-size:9px;color:#0891b2;letter-spacing:.1em;margin-bottom:4px">UPSTREAM</div>
    <div style="font-size:11px;font-weight:600;color:#0f172a;line-height:1.4;word-break:break-all;overflow-wrap:break-word">{upstream}</div>
  </div>
  <div style="font-size:18px;color:#0891b2;flex-shrink:0">→</div>
  <div style="padding:10px 12px;background:#fef3c7;border:2px solid #d97706;border-radius:8px;text-align:center;overflow:hidden">
    <div style="font-size:9px;color:#d97706;letter-spacing:.1em;margin-bottom:4px">COMPANY</div>
    <div style="font-size:11px;font-weight:700;color:#0f172a;line-height:1.4">{company}</div>
  </div>
  <div style="font-size:18px;color:#0891b2;flex-shrink:0">→</div>
  <div style="padding:10px 12px;background:#d1fae5;border:1px solid #059669;border-radius:8px;text-align:center;overflow:hidden">
    <div style="font-size:9px;color:#059669;letter-spacing:.1em;margin-bottom:4px">DOWNSTREAM</div>
    <div style="font-size:11px;font-weight:600;color:#0f172a;line-height:1.4;word-break:break-all;overflow-wrap:break-word">{downstream}</div>
  </div>
</div>'''


def svg_timeline(events: list) -> str:
    """Vertical timeline of events."""
    if not events:
        return ""
    items = []
    for ev in events:
        items.append(
            f'<div style="display:flex;gap:10px;padding:8px 0">'
            f'<div style="width:10px;height:10px;border-radius:50%;background:{COLOR_GOLD};margin-top:4px;flex-shrink:0;'
            f'box-shadow:0 0 0 3px #fef3c7"></div>'
            f'<div style="font-size:11px;color:#1e293b;line-height:1.5">{ev}</div>'
            f'</div>'
        )
    return f'<div style="border-left:2px solid #e2e8f0;padding-left:12px;margin-left:5px">{"".join(items)}</div>'


def svg_bars(values: list, labels: list = None, width: int = 280, height: int = 120, color: str = COLOR_CYAN, show_values: bool = True, overlay_line: list = None, line_color: str = COLOR_GOLD) -> str:
    """Vertical bar chart with optional overlay line."""
    if not values:
        return ""
    n = len(values)
    pad_l, pad_r, pad_t, pad_b = 30, 10, 14, 24
    chart_w = width - pad_l - pad_r
    chart_h = height - pad_t - pad_b
    max_v = max(values + (overlay_line or []) + [0])
    min_v = min(values + (overlay_line or []) + [0])
    span = max(max_v - min_v, 1e-9)
    bar_w = chart_w / n * 0.7
    gap = chart_w / n * 0.3

    bars = []
    vals_txt = []
    labels_txt = []
    for i, v in enumerate(values):
        x = pad_l + i * (chart_w / n) + gap / 2
        bar_h = (v - min_v) / span * chart_h if span else 0
        y = pad_t + chart_h - bar_h
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{color}" rx="2"/>')
        if show_values:
            vals_txt.append(f'<text x="{x + bar_w/2:.1f}" y="{y - 4:.1f}" text-anchor="middle" font-family="Fira Code" font-size="9" fill="#0f172a" font-weight="700">{v}</text>')
        if labels:
            labels_txt.append(f'<text x="{x + bar_w/2:.1f}" y="{pad_t + chart_h + 14}" text-anchor="middle" font-family="Fira Code" font-size="9" fill="#64748b">{labels[i] if i < len(labels) else ""}</text>')

    # y-axis zero line
    y_zero = pad_t + chart_h - (0 - min_v) / span * chart_h if span else pad_t + chart_h
    axis = f'<line x1="{pad_l}" y1="{y_zero:.1f}" x2="{pad_l+chart_w}" y2="{y_zero:.1f}" stroke="#cbd5e1" stroke-width="1"/>'

    # overlay line (e.g. growth rate)
    line_path = ""
    line_dots = ""
    if overlay_line and len(overlay_line) == n:
        pts = []
        for i, v in enumerate(overlay_line):
            x = pad_l + i * (chart_w / n) + chart_w / n / 2
            y = pad_t + chart_h - (v - min_v) / span * chart_h if span else pad_t + chart_h
            pts.append((x, y))
        path_str = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        line_path = f'<path d="{path_str}" fill="none" stroke="{line_color}" stroke-width="2.5"/>'
        line_dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{line_color}"/>' for x, y in pts)

    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  {axis}
  {"".join(bars)}
  {line_path}
  {line_dots}
  {"".join(vals_txt)}
  {"".join(labels_txt)}
</svg>'''


def svg_candlestick(candles: list, width: int = 380, height: int = 180, ma_20: list = None, ma_60: list = None) -> str:
    """Hand-rolled SVG candlestick. candles = [{open, close, high, low, date}, ...]"""
    if not candles:
        return ""
    n = len(candles)
    pad_l, pad_r, pad_t, pad_b = 40, 10, 10, 24
    chart_w = width - pad_l - pad_r
    chart_h = height - pad_t - pad_b
    all_highs = [c["high"] for c in candles]
    all_lows = [c["low"] for c in candles]
    if ma_20:
        all_highs += [v for v in ma_20 if v]
        all_lows += [v for v in ma_20 if v]
    if ma_60:
        all_highs += [v for v in ma_60 if v]
        all_lows += [v for v in ma_60 if v]
    y_max = max(all_highs) * 1.02
    y_min = min(all_lows) * 0.98
    span = max(y_max - y_min, 1e-9)

    def y_of(v):
        return pad_t + chart_h - (v - y_min) / span * chart_h

    cw = chart_w / n * 0.7
    gap = chart_w / n * 0.3

    elems = []
    # grid
    for ring in (0.25, 0.5, 0.75):
        yg = pad_t + chart_h * ring
        elems.append(f'<line x1="{pad_l}" y1="{yg:.1f}" x2="{pad_l+chart_w}" y2="{yg:.1f}" stroke="#f1f5f9" stroke-width="1"/>')

    # y labels
    for frac, v in [(0, y_max), (0.5, (y_max+y_min)/2), (1, y_min)]:
        yt = pad_t + chart_h * frac
        elems.append(f'<text x="{pad_l-5}" y="{yt+3:.1f}" text-anchor="end" font-family="Fira Code" font-size="9" fill="#64748b">{v:.1f}</text>')

    # candles
    for i, c in enumerate(candles):
        x = pad_l + i * (chart_w / n) + gap / 2
        cx = x + cw / 2
        op, cl, hi, lo = c["open"], c["close"], c["high"], c["low"]
        is_up = cl >= op
        color = COLOR_BEAR if is_up else COLOR_BULL  # China convention: red up, green down
        # wick
        elems.append(f'<line x1="{cx:.1f}" y1="{y_of(hi):.1f}" x2="{cx:.1f}" y2="{y_of(lo):.1f}" stroke="{color}" stroke-width="1"/>')
        # body
        top = y_of(max(op, cl))
        bh = max(abs(y_of(cl) - y_of(op)), 1)
        elems.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{cw:.1f}" height="{bh:.1f}" fill="{color}" stroke="{color}" stroke-width="1"/>')

    # MA lines
    def _ma_path(vals, color, label):
        if not vals:
            return ""
        pts = []
        for i, v in enumerate(vals):
            if v is None:
                continue
            x = pad_l + i * (chart_w / n) + cw / 2 + gap / 2
            y = y_of(v)
            pts.append(f"{x:.1f},{y:.1f}")
        if not pts:
            return ""
        return f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round"/>'

    elems.append(_ma_path(ma_20, COLOR_GOLD, "MA20"))
    elems.append(_ma_path(ma_60, COLOR_INDIGO, "MA60"))

    # date labels (first, mid, last)
    if candles and "date" in candles[0]:
        for i in [0, n // 2, n - 1]:
            x = pad_l + i * (chart_w / n) + cw / 2
            elems.append(f'<text x="{x:.1f}" y="{pad_t+chart_h+14}" text-anchor="middle" font-family="Fira Code" font-size="8" fill="#64748b">{candles[i]["date"][-5:]}</text>')

    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="width:100%">
  {"".join(elems)}
</svg>
<div style="display:flex;gap:14px;margin-top:6px;font-family:Fira Code;font-size:9px">
  <span><span style="display:inline-block;width:12px;height:2px;background:{COLOR_GOLD};vertical-align:middle"></span> MA20</span>
  <span><span style="display:inline-block;width:12px;height:2px;background:{COLOR_INDIGO};vertical-align:middle"></span> MA60</span>
</div>'''


def svg_pe_band(pe_history: list, bands: dict = None, width: int = 300, height: int = 140) -> str:
    """PE historical line with percentile bands. bands = {p25, p50, p75, current_idx}"""
    if not pe_history or len(pe_history) < 2:
        return ""
    import numpy as _np
    import statistics
    n = len(pe_history)
    pad_l, pad_r, pad_t, pad_b = 36, 10, 10, 20
    w = width - pad_l - pad_r
    h = height - pad_t - pad_b

    sorted_pe = sorted(pe_history)
    p25 = sorted_pe[int(n * 0.25)]
    p50 = sorted_pe[int(n * 0.5)]
    p75 = sorted_pe[int(n * 0.75)]
    y_max = max(pe_history) * 1.05
    y_min = min(pe_history) * 0.95
    span = max(y_max - y_min, 1e-9)

    def y_of(v):
        return pad_t + h - (v - y_min) / span * h

    # bands (percentile horizontal strips)
    y25 = y_of(p25)
    y50 = y_of(p50)
    y75 = y_of(p75)
    bands_svg = f'''
  <rect x="{pad_l}" y="{pad_t}" width="{w}" height="{y75-pad_t:.1f}" fill="#fee2e2" opacity="0.5"/>
  <rect x="{pad_l}" y="{y75:.1f}" width="{w}" height="{y25-y75:.1f}" fill="#fef3c7" opacity="0.5"/>
  <rect x="{pad_l}" y="{y25:.1f}" width="{w}" height="{pad_t+h-y25:.1f}" fill="#d1fae5" opacity="0.5"/>
  <line x1="{pad_l}" y1="{y25:.1f}" x2="{pad_l+w}" y2="{y25:.1f}" stroke="#059669" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="{pad_l}" y1="{y50:.1f}" x2="{pad_l+w}" y2="{y50:.1f}" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="{pad_l}" y1="{y75:.1f}" x2="{pad_l+w}" y2="{y75:.1f}" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="{pad_l-3}" y="{y25+3:.1f}" text-anchor="end" font-family="Fira Code" font-size="8" fill="#059669">25%</text>
  <text x="{pad_l-3}" y="{y50+3:.1f}" text-anchor="end" font-family="Fira Code" font-size="8" fill="#64748b">50%</text>
  <text x="{pad_l-3}" y="{y75+3:.1f}" text-anchor="end" font-family="Fira Code" font-size="8" fill="#dc2626">75%</text>
    '''

    # line
    pts = []
    for i, v in enumerate(pe_history):
        x = pad_l + i / (n - 1) * w
        y = y_of(v)
        pts.append(f"{x:.1f},{y:.1f}")
    line = f'<polyline points="{" ".join(pts)}" fill="none" stroke="{COLOR_BLUE}" stroke-width="2"/>'

    # current point highlight
    last_x = pad_l + w
    last_y = y_of(pe_history[-1])
    current = f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="5" fill="{COLOR_BLUE}" stroke="#fff" stroke-width="2"/>'
    cur_label = f'<text x="{last_x:.1f}" y="{last_y-10:.1f}" text-anchor="end" font-family="Fira Code" font-size="10" font-weight="700" fill="{COLOR_BLUE}">{pe_history[-1]:.1f}</text>'

    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="width:100%">
  {bands_svg}
  {line}
  {current}
  {cur_label}
</svg>'''


def svg_progress_row(label: str, pct: float, color: str = COLOR_CYAN, suffix: str = "") -> str:
    """Inline labeled progress bar."""
    pct_clamped = max(0, min(100, pct))
    return f'''<div style="display:flex;align-items:center;gap:10px;margin:6px 0">
  <div style="width:70px;font-family:Fira Code;font-size:10px;color:#64748b">{label}</div>
  <div style="flex:1;height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden">
    <div style="width:{pct_clamped}%;height:100%;background:{color};border-radius:4px"></div>
  </div>
  <div style="min-width:50px;text-align:right;font-family:Fira Code;font-size:11px;color:#0f172a;font-weight:700">{pct:.1f}{suffix}</div>
</div>'''


def svg_peer_table(rows: list) -> str:
    """HTML comparison table. rows = [{name, pe, pb, roe, revenue_growth, is_self}, ...]"""
    if not rows:
        return ""
    head = '''<tr style="background:#f8fafc">
  <th style="text-align:left;padding:8px 10px;font-family:Fira Code;font-size:9px;color:#64748b;font-weight:700;border-bottom:2px solid #e2e8f0">公司</th>
  <th style="text-align:right;padding:8px 10px;font-family:Fira Code;font-size:9px;color:#64748b;font-weight:700;border-bottom:2px solid #e2e8f0">PE</th>
  <th style="text-align:right;padding:8px 10px;font-family:Fira Code;font-size:9px;color:#64748b;font-weight:700;border-bottom:2px solid #e2e8f0">PB</th>
  <th style="text-align:right;padding:8px 10px;font-family:Fira Code;font-size:9px;color:#64748b;font-weight:700;border-bottom:2px solid #e2e8f0">ROE</th>
  <th style="text-align:right;padding:8px 10px;font-family:Fira Code;font-size:9px;color:#64748b;font-weight:700;border-bottom:2px solid #e2e8f0">营收增速</th>
</tr>'''
    body = ""
    for r in rows:
        is_self = r.get("is_self", False)
        row_style = 'background:#fef3c7;font-weight:700' if is_self else 'background:#ffffff'
        body += f'''<tr style="{row_style}">
  <td style="padding:8px 10px;font-family:Fira Sans;font-size:12px;color:#0f172a;border-bottom:1px solid #f1f5f9">{'⭐ ' if is_self else ''}{r.get("name", "")}</td>
  <td style="text-align:right;padding:8px 10px;font-family:Fira Code;font-size:11px;color:#0f172a;border-bottom:1px solid #f1f5f9">{r.get("pe", "—")}</td>
  <td style="text-align:right;padding:8px 10px;font-family:Fira Code;font-size:11px;color:#0f172a;border-bottom:1px solid #f1f5f9">{r.get("pb", "—")}</td>
  <td style="text-align:right;padding:8px 10px;font-family:Fira Code;font-size:11px;color:#0f172a;border-bottom:1px solid #f1f5f9">{r.get("roe", "—")}</td>
  <td style="text-align:right;padding:8px 10px;font-family:Fira Code;font-size:11px;color:#0f172a;border-bottom:1px solid #f1f5f9">{r.get("revenue_growth", "—")}</td>
</tr>'''
    return f'<table style="width:100%;border-collapse:collapse;font-family:Fira Sans">{head}{body}</table>'


def svg_unlock_timeline(unlocks: list, width: int = 280, height: int = 100) -> str:
    """Future unlock timeline: list of {date, amount_亿}."""
    if not unlocks:
        return '<div style="text-align:center;color:#94a3b8;font-size:11px;padding:10px">未来 12 个月无解禁</div>'
    n = len(unlocks)
    pad_l, pad_r, pad_t, pad_b = 20, 10, 16, 24
    w = width - pad_l - pad_r
    h = height - pad_t - pad_b
    max_a = max(u.get("amount", 0) for u in unlocks) or 1
    bar_w = w / n * 0.6
    gap = w / n * 0.4
    bars = []
    for i, u in enumerate(unlocks):
        amt = u.get("amount", 0)
        date = u.get("date", "")
        x = pad_l + i * (w / n) + gap / 2
        bar_h = amt / max_a * h
        y = pad_t + h - bar_h
        color = COLOR_BEAR if amt > max_a * 0.5 else COLOR_GOLD
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{color}" rx="2"/>')
        bars.append(f'<text x="{x + bar_w/2:.1f}" y="{y - 3:.1f}" text-anchor="middle" font-family="Fira Code" font-size="9" fill="#0f172a" font-weight="700">{amt}</text>')
        bars.append(f'<text x="{x + bar_w/2:.1f}" y="{pad_t+h+14}" text-anchor="middle" font-family="Fira Code" font-size="8" fill="#64748b">{date}</text>')
    axis = f'<line x1="{pad_l}" y1="{pad_t+h}" x2="{pad_l+w}" y2="{pad_t+h}" stroke="#cbd5e1"/>'
    return f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="width:100%">{axis}{"".join(bars)}</svg>'


def svg_dividend_combo(years: list, amounts: list, yields: list, width: int = 300, height: int = 140) -> str:
    """Dividend history: bars for amount + line for yield."""
    if not years or not amounts:
        return ""
    n = len(years)
    pad_l, pad_r, pad_t, pad_b = 36, 40, 14, 24
    w = width - pad_l - pad_r
    h = height - pad_t - pad_b
    max_a = max(amounts) or 1
    max_y = max(yields) if yields else 5
    bar_w = w / n * 0.55
    gap = w / n * 0.45

    bars = []
    for i, a in enumerate(amounts):
        x = pad_l + i * (w / n) + gap / 2
        bar_h = a / max_a * h
        y = pad_t + h - bar_h
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{COLOR_CYAN}" rx="2"/>')
        bars.append(f'<text x="{x+bar_w/2:.1f}" y="{y-3:.1f}" text-anchor="middle" font-family="Fira Code" font-size="9" fill="#0f172a" font-weight="700">{a}</text>')
        bars.append(f'<text x="{x+bar_w/2:.1f}" y="{pad_t+h+14}" text-anchor="middle" font-family="Fira Code" font-size="9" fill="#64748b">{years[i]}</text>')

    # yield line (right axis)
    if yields:
        pts = []
        for i, y in enumerate(yields):
            x = pad_l + i * (w / n) + w / n / 2
            yy = pad_t + h - y / max_y * h
            pts.append((x, yy))
        line = f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)}" fill="none" stroke="{COLOR_GOLD}" stroke-width="2.5"/>'
        dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{COLOR_GOLD}"/>' for x, y in pts)
        bars.append(line)
        bars.append(dots)
        # right axis label
        bars.append(f'<text x="{pad_l+w+4}" y="{pad_t+10}" font-family="Fira Code" font-size="9" fill="{COLOR_GOLD}">{max_y:.1f}%</text>')
        bars.append(f'<text x="{pad_l+w+4}" y="{pad_t+h}" font-family="Fira Code" font-size="9" fill="{COLOR_GOLD}">0%</text>')

    return f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="width:100%">{"".join(bars)}</svg>'


def svg_institutional_quarters(data: dict, width: int = 300, height: int = 120) -> str:
    """Stacked/grouped bar of institutional holdings over quarters.
    data = {'quarters': ['23Q2', '23Q3', ...], 'fund': [...], 'qfii': [...], 'shehui': [...]}"""
    quarters = data.get("quarters", [])
    if not quarters:
        return ""
    series = [
        ("公募", data.get("fund", []), COLOR_CYAN),
        ("QFII", data.get("qfii", []), COLOR_BLUE),
        ("社保", data.get("shehui", []), COLOR_GOLD),
    ]
    n = len(quarters)
    pad_l, pad_r, pad_t, pad_b = 10, 10, 16, 22
    w = width - pad_l - pad_r
    h = height - pad_t - pad_b
    all_vals = [v for _, vals, _ in series for v in vals if v is not None] + [0]
    max_v = max(all_vals) or 1

    bar_w = w / n * 0.28
    group_gap = w / n * 0.16

    elems = []
    for i in range(n):
        bx = pad_l + i * (w / n) + group_gap / 2
        for si, (_, vals, col) in enumerate(series):
            if i >= len(vals):
                continue
            v = vals[i]
            bar_h = v / max_v * h
            x = bx + si * bar_w
            y = pad_t + h - bar_h
            elems.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-0.5:.1f}" height="{bar_h:.1f}" fill="{col}" rx="1"/>')
        elems.append(f'<text x="{bx + 1.5*bar_w:.1f}" y="{pad_t+h+14}" text-anchor="middle" font-family="Fira Code" font-size="9" fill="#64748b">{quarters[i]}</text>')

    legend = f'''<div style="display:flex;gap:10px;margin-top:4px;font-family:Fira Code;font-size:9px">
  <span style="color:{COLOR_CYAN}">■ 公募</span>
  <span style="color:{COLOR_BLUE}">■ QFII</span>
  <span style="color:{COLOR_GOLD}">■ 社保</span>
</div>'''
    return f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="width:100%">{"".join(elems)}</svg>{legend}'


def svg_thermometer(value: int, max_val: int = 100, label: str = "") -> str:
    """Heat thermometer (vertical)."""
    pct = min(100, max(0, value / max_val * 100))
    color = COLOR_BEAR if value > 80 else COLOR_GOLD if value > 50 else COLOR_BULL
    return f'''<div style="display:flex;align-items:center;gap:14px">
  <div style="width:24px;height:120px;background:#f1f5f9;border:1px solid #cbd5e1;border-radius:12px;position:relative;overflow:hidden">
    <div style="position:absolute;bottom:0;left:0;right:0;height:{pct}%;background:linear-gradient(0deg,{color},{color}cc);border-radius:0 0 12px 12px;transition:height 1s"></div>
  </div>
  <div>
    <div style="font-family:Fira Sans;font-weight:900;font-size:32px;color:{color};line-height:1">{value}</div>
    <div style="font-family:Fira Code;font-size:9px;color:#64748b;letter-spacing:.1em">{label}</div>
  </div>
</div>'''

