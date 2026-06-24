"""LhbRenderer · 龙虎榜 · 对应 16_lhb."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class LhbRenderer(SectionRenderer):
    section_id = "lhb"
    section_title = "🐲 龙虎榜"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        count_30d = d.get("lhb_count_30d") or 0
        records = d.get("lhb_records") or []
        matched_youzi = d.get("matched_youzi") or []
        inst_vs_youzi = d.get("inst_vs_youzi") or {}

        if count_30d == 0 and not records and not matched_youzi:
            return self.render_gap(ctx, "近 30 日未上龙虎榜")

        youzi_html = ""
        if matched_youzi:
            names = [m if isinstance(m, str) else m.get("name", "") for m in matched_youzi[:5]]
            youzi_html = f'<div><strong>游资身影</strong>：{"、".join(n for n in names if n)}</div>'

        inst_net = inst_vs_youzi.get("institutional_net") if isinstance(inst_vs_youzi, dict) else None
        youzi_buy = inst_vs_youzi.get("youzi_buy") if isinstance(inst_vs_youzi, dict) else None

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div style="font-size:13px">
    <div>近 30 日上榜 · <strong>{count_30d}</strong> 次</div>
    {youzi_html}
    <div>机构净买入：<strong>{inst_net or "—"}</strong> · 游资净买入：<strong>{youzi_buy or "—"}</strong></div>
  </div>
</section>'''
