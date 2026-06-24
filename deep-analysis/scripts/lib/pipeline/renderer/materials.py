"""MaterialsRenderer · 原材料 · 对应 8_materials."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class MaterialsRenderer(SectionRenderer):
    section_id = "materials"
    section_title = "⚙️ 原材料与成本"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        core = d.get("core_material") or "—"
        price_trend = d.get("price_trend") or "—"
        cost_share = d.get("cost_share") or "—"
        import_dep = d.get("import_dep") or "—"
        details = d.get("materials_detail") or []

        if core == "—" and price_trend == "—" and not details:
            return self.render_gap(ctx, "原材料数据不足")

        detail_html = ""
        if details:
            items = []
            for m in details[:5]:
                if isinstance(m, dict):
                    name = m.get("name") or "—"
                    trend = m.get("price_change") or m.get("trend") or "—"
                    items.append(f'<li><strong>{name}</strong> · {trend}</li>')
            if items:
                detail_html = f'<ul style="font-size:12px">{"".join(items)}</ul>'

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div style="font-size:13px">
    <div><strong>核心原材料</strong>：{core}</div>
    <div><strong>价格走势</strong>：{price_trend}</div>
    <div><strong>成本占比</strong>：{cost_share}</div>
    <div><strong>进口依赖度</strong>：{import_dep}</div>
  </div>
  {detail_html}
</section>'''
