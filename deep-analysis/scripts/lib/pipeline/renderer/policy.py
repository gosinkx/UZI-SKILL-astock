"""PolicyRenderer · 政策与监管 · 对应 13_policy."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


_SENTIMENT_EMOJI = {"积极": "🟢", "中性": "🟡", "收紧": "🔴", "—": "⚪"}


class PolicyRenderer(SectionRenderer):
    section_id = "policy"
    section_title = "📜 政策与监管"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        items = [
            ("政策方向", d.get("policy_dir") or "—"),
            ("补贴", d.get("subsidy") or "—"),
            ("监管", d.get("monitoring") or "—"),
            ("反垄断", d.get("anti_trust") or "—"),
        ]
        html = []
        for label, val in items:
            emoji = _SENTIMENT_EMOJI.get(val, "⚪")
            html.append(f'<div><strong>{label}</strong>：{emoji} {val}</div>')

        year = d.get("year") or ""
        industry = d.get("industry") or ctx.meta.get("industry") or ""

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title} · {industry} {year}</h2>
  <div style="font-size:13px;display:grid;grid-template-columns:1fr 1fr;gap:6px">
    {"".join(html)}
  </div>
</section>'''
