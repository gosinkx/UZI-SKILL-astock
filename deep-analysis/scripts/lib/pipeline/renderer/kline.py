"""KlineRenderer · K 线 + 技术指标 · 对应 2_kline."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


def _fmt_pct(v, default="—"):
    if v is None or v == "":
        return default
    if isinstance(v, str):
        return v
    try:
        x = float(v)
        return f"{'+' if x > 0 else ''}{x:.1f}%"
    except (ValueError, TypeError):
        return str(v) if v else default


class KlineRenderer(SectionRenderer):
    section_id = "kline"
    section_title = "📈 K 线走势与技术指标"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        pc_1m = _fmt_pct(d.get("price_change_1m"))
        pc_3m = _fmt_pct(d.get("price_change_3m"))
        pc_6m = _fmt_pct(d.get("price_change_6m"))
        pc_1y = _fmt_pct(d.get("price_change_1y"))
        rsi = d.get("rsi") or "—"
        ma5 = d.get("ma5") or "—"
        ma20 = d.get("ma20") or "—"
        ma60 = d.get("ma60") or "—"
        vol_ratio = d.get("vol_ratio") or "—"
        bb_status = d.get("bollinger_status") or "—"

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div class="kline-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
    <div><div class="label">近 1 月</div><div class="value">{pc_1m}</div></div>
    <div><div class="label">近 3 月</div><div class="value">{pc_3m}</div></div>
    <div><div class="label">近 6 月</div><div class="value">{pc_6m}</div></div>
    <div><div class="label">近 1 年</div><div class="value">{pc_1y}</div></div>
    <div><div class="label">RSI</div><div class="value">{rsi}</div></div>
    <div><div class="label">MA5/MA20/MA60</div><div class="value">{ma5}/{ma20}/{ma60}</div></div>
    <div><div class="label">量比</div><div class="value">{vol_ratio}</div></div>
    <div><div class="label">布林带</div><div class="value">{bb_status}</div></div>
  </div>
</section>'''
