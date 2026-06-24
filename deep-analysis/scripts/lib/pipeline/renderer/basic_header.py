"""BasicHeaderRenderer · 报告头部基础信息 · 对应 0_basic."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class BasicHeaderRenderer(SectionRenderer):
    section_id = "basic_header"
    section_title = ""  # 头部不需要标题 · 公司名已在全局 header

    def render_full(self, ctx: RenderContext) -> str:
        data = ctx.data
        name = data.get("name") or ctx.name or "—"
        full_name = data.get("full_name") or "—"
        industry = data.get("industry") or "—"
        price = data.get("price") or "—"
        market_cap = data.get("market_cap") or "—"
        pe_ttm = data.get("pe_ttm") or "—"
        pe_static = data.get("pe_static") or "—"
        pb = data.get("pb") or "—"
        eps = data.get("eps") or "—"
        listed = data.get("listed_date") or "—"
        actual = data.get("actual_controller") or "—"
        main_business = data.get("main_business") or "—"

        return f'''<section id="{self.section_id}">
  <div class="basic-header">
    <h1>{name} <small style="color:#64748b;font-size:14px">{ctx.ticker}</small></h1>
    <div style="color:#475569;font-size:12px">{full_name} · {industry}</div>
    <div class="basic-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px">
      <div><div class="label">现价</div><div class="value"><strong>¥{price}</strong></div></div>
      <div><div class="label">市值</div><div class="value">{market_cap}</div></div>
      <div><div class="label">PE(TTM)</div><div class="value">{pe_ttm}</div></div>
      <div><div class="label">PB</div><div class="value">{pb}</div></div>
      <div><div class="label">EPS</div><div class="value">{eps}</div></div>
      <div><div class="label">PE(静)</div><div class="value">{pe_static}</div></div>
      <div><div class="label">上市</div><div class="value">{listed}</div></div>
      <div><div class="label">实控人</div><div class="value" style="font-size:11px">{actual[:30]}</div></div>
    </div>
    <div style="margin-top:8px;font-size:12px;color:#475569">
      <strong>主营</strong>：{main_business[:200]}
    </div>
  </div>
</section>'''
