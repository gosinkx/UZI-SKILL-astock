"""GovernanceRenderer · 公司治理 · 对应 11_governance."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class GovernanceRenderer(SectionRenderer):
    section_id = "governance"
    section_title = "⚖️ 公司治理"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        pledge = d.get("pledge") or "—"
        insider_1y = d.get("insider_trades_1y") or "—"
        chairman_turnover = d.get("chairman_turnover") or "—"

        if pledge == "—" and insider_1y == "—" and chairman_turnover == "—":
            return self.render_gap(ctx, "治理数据不足")

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div style="font-size:13px">
    <div><strong>股权质押</strong>：{pledge}</div>
    <div><strong>近 1 年内部人交易</strong>：{insider_1y}</div>
    <div><strong>董事长变更</strong>：{chairman_turnover}</div>
  </div>
</section>'''
