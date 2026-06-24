"""PeersRenderer · 同行对比 section · 对应 4_peers.

v2.12.1 教训：peer_table 常空（push2 反爬）· render 需要 3 态
- full: 多家同行 + PE/PB 对比
- lite: 只有公司自己 + fallback 原因
- gap: 完全空
"""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class PeersRenderer(SectionRenderer):
    section_id = "peers"
    section_title = "🏭 同行对比"

    def render_full(self, ctx: RenderContext) -> str:
        data = ctx.data
        peer_table = data.get("peer_table") or []
        peer_comparison = data.get("peer_comparison") or []

        if not peer_table and not peer_comparison:
            return self.render_gap(ctx, "同行抓取失败（push2/xueqiu 反爬）")

        rows = []
        for p in (peer_comparison or peer_table)[:12]:
            if not isinstance(p, dict):
                continue
            rows.append(f'''<tr>
  <td>{p.get("name") or p.get("code", "—")}</td>
  <td>{p.get("market_cap") or p.get("mcap") or "—"}</td>
  <td>{p.get("pe_ttm") or p.get("pe") or "—"}</td>
  <td>{p.get("pb") or "—"}</td>
  <td>{p.get("roe") or "—"}</td>
</tr>''')

        if not rows:
            return self.render_gap(ctx, "同行数据为空")

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <table class="peers-table" style="width:100%;border-collapse:collapse">
    <thead>
      <tr><th>公司</th><th>市值</th><th>PE(TTM)</th><th>PB</th><th>ROE</th></tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</section>'''
