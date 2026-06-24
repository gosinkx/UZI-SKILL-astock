"""FuturesRenderer · 期货关联 · 对应 9_futures."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class FuturesRenderer(SectionRenderer):
    section_id = "futures"
    section_title = "📦 期货联动"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        contract = d.get("linked_contract") or "—"
        price_trend = d.get("price_trend") or "—"
        inventory = d.get("inventory") or "—"

        if "无直接" in str(contract) or contract == "—":
            return self.render_gap(ctx, "非大宗商品相关行业")

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div style="font-size:13px">
    <div><strong>关联合约</strong>：{contract}</div>
    <div><strong>价格走势</strong>：{price_trend}</div>
    <div><strong>库存</strong>：{inventory}</div>
  </div>
</section>'''
