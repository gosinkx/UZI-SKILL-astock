"""MacroRenderer · 宏观环境 · 对应 3_macro."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class MacroRenderer(SectionRenderer):
    section_id = "macro"
    section_title = "🌏 宏观环境"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        rows = [
            ("利率周期", d.get("rate_cycle")),
            ("汇率走势", d.get("fx_trend")),
            ("地缘风险", d.get("geo_risk")),
            ("大宗商品", d.get("commodity")),
            ("成长动能", d.get("growth_momentum")),
        ]
        items = "".join(
            f'<div class="macro-item"><strong>{label}</strong>：{v or "—"}</div>'
            for label, v in rows if v
        )
        if not items:
            return self.render_gap(ctx, "宏观数据不足")
        return f'<section id="{self.section_id}"><h2>{self.section_title}</h2><div class="macro-grid">{items}</div></section>'
