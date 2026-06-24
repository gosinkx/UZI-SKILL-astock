"""report.panel_cards · 51 评委面板相关渲染 · v3.2 从 assemble_report.py 抽离.

### 内容
- `GROUP_LABELS` · 7 流派中文标签 (A 价值 / B 成长 / ...）
- `render_jury_seat(inv)` · 单个评委头像卡片
- `render_chat_message(inv)` · 微信气泡式评论
- `render_vote_bars(vote_dist)` · 投票分布柱状图
- `render_top3_bulls/bears(investors)` · 前 3 看多 / 看空
- `_render_top3_by_signal` · helper
- `render_risks(risks)` · 风险点列表
- `_li` · 公共 list-item helper

### 为什么搬出来
Panel (51 评委) 相关渲染 ~155 行独立块 · 不与 dim_card 或 institutional 耦合.

### 向后兼容
assemble_report.py 做 re-export · 所有历史调用不变.
"""
from __future__ import annotations


def _safe(v, default="—"):
    """local helper · 避免循环 import assemble_report."""
    if v is None or v == "" or v == "—" or v == "nan":
        return default
    return v


GROUP_LABELS = {"A": "价值", "B": "成长", "C": "宏观", "D": "技术", "E": "中国", "F": "游资", "G": "量化",
                "H": "科技", "I": "卡位"}  # v3.8.1 · 补 H/I (之前 H/I 评委显示裸字母)


def render_jury_seat(inv: dict) -> str:
    """One judge seat on the judging board (50 灯). Click → scroll to chat message."""
    sig = inv.get("signal", "neutral")
    name = (inv.get("name") or "")[:4]
    score = inv.get("score", 0)
    inv_id = inv["investor_id"]
    return f'''<div class="seat {sig}" data-group="{inv.get("group", "")}" data-target="msg-{inv_id}" title="{inv.get("name", "")} · {inv.get("verdict", "")} · 点击查看完整结论">
  <img src="avatars/{inv_id}.svg" class="seat-avatar" alt="">
  <div class="seat-name">{name}</div>
  <div class="seat-score">{score}</div>
</div>'''


def _li(items: list) -> str:
    if not items:
        return ""
    return "".join(f"<li>{x}</li>" for x in items)


def render_chat_message(inv: dict) -> str:
    """One chat bubble + expandable full conclusion."""
    sig = inv.get("signal", "neutral")
    group = inv.get("group", "")
    group_label = GROUP_LABELS.get(group, group)
    score = inv.get("score", 0)
    confidence = inv.get("confidence", 0)
    reasoning = _safe(inv.get("reasoning") or inv.get("comment"), "—")
    comment = _safe(inv.get("comment"), "")
    verdict = _safe(inv.get("verdict"), "—")
    pass_items = inv.get("pass") or []
    fail_items = inv.get("fail") or []
    ideal_price = inv.get("ideal_price")
    period = _safe(inv.get("period"), "—")
    inv_id = inv["investor_id"]

    bubble_main = f'<div class="msg-reasoning">{reasoning}</div>'
    if comment and comment != reasoning:
        bubble_main += f'<div class="msg-comment">💬 "{comment}"</div>'

    # Full conclusion (collapsed by default, click to expand)
    pass_html = f'<div class="conc-block"><div class="conc-label">✅ 命中</div><ul>{_li(pass_items)}</ul></div>' if pass_items else ""
    fail_html = f'<div class="conc-block"><div class="conc-label">❌ 未命中</div><ul>{_li(fail_items)}</ul></div>' if fail_items else ""
    price_html = f'<div class="conc-row"><span>🎯 理想买入价</span><strong>¥{ideal_price}</strong></div>' if ideal_price else ""

    # v2.8 · 因地制宜：每个评委自己方法论回答的 3 个问题（time_horizon / position / 翻盘条件）
    th = _safe(inv.get("time_horizon"), "")
    ps = _safe(inv.get("position_sizing"), "")
    wc = _safe(inv.get("what_would_change_my_mind"), "")
    profile_rows = []
    if th and th != "—":
        profile_rows.append(f'<div class="conc-row"><span>⏱ 时间框架</span><em>{th}</em></div>')
    if ps and ps != "—":
        profile_rows.append(f'<div class="conc-row"><span>💰 仓位风格</span><em>{ps}</em></div>')
    if wc and wc != "—":
        profile_rows.append(f'<div class="conc-row"><span>🔄 翻盘条件</span><em>{wc}</em></div>')
    profile_html = (
        f'<div class="conc-block"><div class="conc-label">🧭 我的方法论</div>{"".join(profile_rows)}</div>'
        if profile_rows else ""
    )

    return f'''<div class="chat-msg {sig}" data-group="{group}" id="msg-{inv_id}">
  <img src="avatars/{inv_id}.svg" class="msg-avatar" alt="">
  <div class="msg-body">
    <div class="msg-meta">
      <span class="msg-name">{inv.get("name", "")}</span>
      <span class="msg-group-tag">{group} · {group_label}</span>
      <span class="msg-signal-dot"></span>
      <span class="msg-score-badge">{score}分</span>
      <span class="msg-confidence">conf {confidence}</span>
    </div>
    <div class="msg-bubble">
      {bubble_main}
      <div class="msg-verdict">▸ {verdict} · 周期 {period}</div>
      <details class="msg-details">
        <summary>展开完整结论 ▼</summary>
        <div class="conc-content">
          {pass_html}
          {fail_html}
          {price_html}
          {profile_html}
        </div>
      </details>
    </div>
  </div>
</div>'''


def render_vote_bars(vote_dist: dict) -> str:
    labels = [
        ("强烈买入", "strongly_buy", "var(--bull-green)"),
        ("买入", "buy", "var(--bull-green)"),
        ("关注", "watch", "var(--neon-gold)"),
        ("观望", "wait", "var(--text-dim)"),
        ("回避", "avoid", "var(--bear-red)"),
    ]
    total = sum(vote_dist.values()) or 1
    rows = []
    for cn, key, color in labels:
        count = vote_dist.get(key, 0)
        pct = count / total * 100
        rows.append(
            f'<div class="sc-vote-row">'
            f'<span style="width: 140px">{cn}</span>'
            f'<div class="bar"><div class="fill" style="width:{pct:.0f}%; background:{color}"></div></div>'
            f'<span style="width: 60px; text-align: right">{count} 人</span>'
            f"</div>"
        )
    return "\n".join(rows)


def render_top3_bulls(investors: list[dict]) -> str:
    return _render_top3_by_signal(investors, "bullish", "无看多评委 · 51 人整体倾向中性")


def render_top3_bears(investors: list[dict]) -> str:
    """v2.9.1 对称 render_top3_bulls 的 bear 版。share-card 原先只有 bulls 不对称。"""
    return _render_top3_by_signal(investors, "bearish", "无看空评委 · 51 人整体倾向中性")


def _render_top3_by_signal(investors: list[dict], target_signal: str, empty_msg: str) -> str:
    """v2.9.1 · 提取公共逻辑 + 空时给友好提示而不是 3 个空 div"""
    hits = sorted(
        [i for i in investors if i.get("signal") == target_signal],
        key=lambda x: x.get("score", 0),
        reverse=(target_signal == "bullish"),  # bullish 按分降序；bearish 按分升序
    )[:3]
    if not hits:
        # 空时整块返一个提示，不再 fill 3 个空 div（那是"缺失"的视觉症状）
        return (
            f'<div class="sc-best-empty" style="grid-column:1/-1;text-align:center;'
            f'color:#94a3b8;font-size:12px;padding:16px">{empty_msg}</div>'
        )
    cells = []
    for inv in hits:
        cells.append(
            f'<div class="sc-best-cell">'
            f'<img src="avatars/{inv["investor_id"]}.svg">'
            f'<div class="name">{inv.get("name")}</div>'
            f'<div class="score-num">{inv.get("score", 0)}</div>'
            f"</div>"
        )
    # 不足 3 个时给半透明 placeholder 而不是空白格
    while len(cells) < 3:
        cells.append(
            '<div class="sc-best-cell" style="opacity:0.2">'
            '<div style="font-size:12px;color:#94a3b8">—</div></div>'
        )
    return "\n".join(cells)


def render_risks(risks: list[str]) -> str:
    return "\n".join(f"<li>{r}</li>" for r in risks)
