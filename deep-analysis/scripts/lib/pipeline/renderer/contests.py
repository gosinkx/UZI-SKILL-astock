"""ContestsRenderer · 实盘大赛 · 大V组合 · 对应 19_contests."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class ContestsRenderer(SectionRenderer):
    section_id = "contests"
    section_title = "🏆 实盘大赛 / 大V 持仓"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        xq_cubes = d.get("xueqiu_cubes") or []
        tgb = d.get("tgb_mentions") or 0
        ths_simu = d.get("ths_simu") or []
        dpswang = d.get("dpswang") or []
        summary = d.get("summary") or ""

        if not any([xq_cubes, tgb, ths_simu, dpswang]) and not summary:
            return self.render_gap(ctx, "实盘 / 大V 数据不足")

        xq_html = ""
        if xq_cubes:
            xq_html = f'<div><strong>雪球组合</strong> · 检到 <strong>{len(xq_cubes)}</strong> 个</div>'

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div style="font-size:13px">
    {xq_html}
    <div>淘股吧提及 · <strong>{tgb}</strong> 次</div>
    <div>同花顺实盘 · <strong>{len(ths_simu) if isinstance(ths_simu, list) else 0}</strong> 个</div>
    <div>大盘视角王 · <strong>{len(dpswang) if isinstance(dpswang, list) else 0}</strong> 条</div>
    {f'<div style="margin-top:6px;color:#475569">{summary[:200]}</div>' if summary else ''}
  </div>
</section>'''
