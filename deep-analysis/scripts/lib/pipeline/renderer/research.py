"""ResearchRenderer · 研报评级 · 对应 6_research."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class ResearchRenderer(SectionRenderer):
    section_id = "research"
    section_title = "📝 研究报告与评级"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        coverage = d.get("coverage") or d.get("coverage_count") or d.get("report_count") or 0
        buy_pct = d.get("buy_rating_pct") or "—"
        tp_avg = d.get("target_price_avg") or d.get("target_avg") or "—"
        consensus_eps = d.get("consensus_eps_2026") or "—"
        brokers = d.get("brokers") or []
        recent = d.get("recent_reports") or []

        if not coverage and not brokers and not recent:
            return self.render_gap(ctx, "无研报覆盖数据")

        recent_html = ""
        if recent:
            items = "".join(
                f'<li>{r.get("broker", "")} · {r.get("date", "")} · {r.get("title", "") or r.get("rating", "")}</li>'
                for r in recent[:5] if isinstance(r, dict)
            )
            if items:
                recent_html = f'<div><strong>近期研报</strong><ul style="font-size:12px">{items}</ul></div>'

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div class="research-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
    <div><div class="label">覆盖券商</div><div class="value">{coverage}</div></div>
    <div><div class="label">买入占比</div><div class="value">{buy_pct}</div></div>
    <div><div class="label">目标价均值</div><div class="value">{tp_avg}</div></div>
    <div><div class="label">一致 EPS</div><div class="value">{consensus_eps}</div></div>
  </div>
  {recent_html}
</section>'''
