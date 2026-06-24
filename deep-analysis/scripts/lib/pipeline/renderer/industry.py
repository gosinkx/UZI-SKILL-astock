"""IndustryRenderer · 行业景气 section · 对应 7_industry.

v2.12.1 教训：growth/tam/penetration 常 "—" · dynamic_snippets 里有但没抽出来
render 显示已有数据 + 标注 gap.
"""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class IndustryRenderer(SectionRenderer):
    section_id = "industry"
    section_title = "🏢 行业景气"

    def render_full(self, ctx: RenderContext) -> str:
        data = ctx.data
        industry = data.get("industry") or ctx.meta.get("industry") or "—"
        growth = data.get("growth") or "—"
        tam = data.get("tam") or "—"
        penetration = data.get("penetration") or "—"
        ind_pe = data.get("industry_pe") or "—"
        ind_pb = data.get("industry_pb") or "—"

        cninfo = data.get("cninfo_metrics") or {}
        pe_weighted = cninfo.get("industry_pe_weighted")
        total_mcap = cninfo.get("total_mcap_yi")
        company_count = cninfo.get("company_count")

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title} · {industry}</h2>
  <div class="industry-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">
    <div class="industry-metric"><div class="label">行业增速</div><div class="value">{growth}</div></div>
    <div class="industry-metric"><div class="label">TAM 市场空间</div><div class="value">{tam}</div></div>
    <div class="industry-metric"><div class="label">渗透率</div><div class="value">{penetration}</div></div>
    <div class="industry-metric"><div class="label">行业 PE</div><div class="value">{ind_pe}</div></div>
    <div class="industry-metric"><div class="label">行业 PB</div><div class="value">{ind_pb}</div></div>
    <div class="industry-metric"><div class="label">PE 加权（cninfo）</div><div class="value">{pe_weighted or '—'}</div></div>
  </div>
  <div style="margin-top:8px;color:#64748b;font-size:12px">
    行业公司数：{company_count or '—'} · 总市值：{f"{total_mcap:.0f} 亿" if total_mcap else "—"}
  </div>
</section>'''
