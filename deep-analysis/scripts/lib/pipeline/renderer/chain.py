"""ChainRenderer · 产业链上下游 · 对应 5_chain."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


def _list_or_dash(items, limit=5):
    if not items:
        return "—"
    if isinstance(items, str):
        return items[:200]
    if isinstance(items, list):
        vals = [str(x) for x in items[:limit] if x]
        return "、".join(vals) if vals else "—"
    return str(items)[:200]


class ChainRenderer(SectionRenderer):
    section_id = "chain"
    section_title = "🔗 产业链上下游"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        upstream = d.get("upstream")
        downstream = d.get("downstream")
        client_conc = d.get("client_concentration") or "—"
        supplier_conc = d.get("supplier_concentration") or "—"
        main_biz = d.get("main_business_breakdown") or []
        products = d.get("products") or []

        if not any([upstream, downstream, main_biz, products]):
            return self.render_gap(ctx, "产业链数据不足")

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div class="chain-table" style="display:grid;grid-template-columns:auto 1fr;gap:6px;font-size:13px">
    <strong>上游</strong><span>{_list_or_dash(upstream)}</span>
    <strong>下游</strong><span>{_list_or_dash(downstream)}</span>
    <strong>主要产品</strong><span>{_list_or_dash(products)}</span>
    <strong>客户集中度</strong><span>{client_conc}</span>
    <strong>供应商集中度</strong><span>{supplier_conc}</span>
  </div>
</section>'''
