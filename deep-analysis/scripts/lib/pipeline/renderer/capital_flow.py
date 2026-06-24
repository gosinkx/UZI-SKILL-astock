"""CapitalFlowRenderer · 主力资金 / 北向 / 融资 · 对应 12_capital_flow."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class CapitalFlowRenderer(SectionRenderer):
    section_id = "capital_flow"
    section_title = "💰 资金流向"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        main_20d = d.get("main_fund_flow_20d") or []
        north = d.get("northbound") or {}
        margin = d.get("margin_recent") or []
        holder_hist = d.get("holder_count_history") or []
        inst_hist = d.get("institutional_history") or {}
        block_trades = d.get("block_trades_recent") or []
        unlock = d.get("unlock_recent") or []

        if not any([main_20d, north, margin, holder_hist, inst_hist, block_trades]):
            return self.render_gap(ctx, "资金流向数据不足")

        sections = []
        if main_20d:
            sections.append(f'<div>主力资金 20 日流向 · <strong>{len(main_20d)}</strong> 条记录</div>')
        if north:
            total = north.get("net_20d") or north.get("total") or "—"
            sections.append(f'<div>北向 · {total}</div>')
        if margin:
            sections.append(f'<div>融资 · <strong>{len(margin)}</strong> 条记录</div>')
        if holder_hist:
            sections.append(f'<div>股东户数历史 · <strong>{len(holder_hist)}</strong> 期</div>')
        if block_trades:
            sections.append(f'<div>近期大宗交易 · <strong>{len(block_trades)}</strong> 笔</div>')
        if unlock:
            sections.append(f'<div>解禁日历 · <strong>{len(unlock)}</strong> 条</div>')

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div style="font-size:13px;display:grid;grid-template-columns:1fr 1fr;gap:6px">
    {"".join(sections)}
  </div>
</section>'''
