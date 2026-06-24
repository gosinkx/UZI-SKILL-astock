# Task 5 · 报告组装

把 `synthesis.json` + `dimensions.json` + `panel.json` 装配成 3 个产物：
1. `full-report.html` — 16:9 沉浸式仪表盘（Cinematic Sci-Fi）
2. `share-card.png` — 1080×1920 朋友圈竖图战报
3. `war-report.png` — 16:9 黄金分割截图（微信群/Twitter）
4. `one-liner.txt` — 一句话短文本

## ⛔ 禁止清单（违反必须重写）

| 禁止 | 必须 |
|---|---|
| "基本面良好" | "ROE 连续 5 年 >15%，毛利率 22%" |
| "值得关注" | "比 80% 同行便宜，但 K 线刚走出 Stage 1" |
| "前景广阔" | "TAM 200 亿，公司份额 12%，三年后看 25%" |
| "存在风险" | 列出具体维度名 + 具体数字 |
| 复制模板话 | 每只票必须有不同的金句 |

## 装配流程

```bash
python scripts/assemble_report.py {ticker}
# → reports/{ticker}_{date}/full-report.html

python scripts/render_share_card.py {ticker}
# → reports/{ticker}_{date}/share-card.png  (1080x1920)

python scripts/render_war_report.py {ticker}
# → reports/{ticker}_{date}/war-report.png  (1920x1080)
```

PNG 由 Playwright 截 HTML 内的隐藏 div：
- `#share-card` → 1080×1920，朋友圈
- `#war-report` → 1920×1080，微信群/Twitter
- 截图前等待字体加载完成 `await page.evaluate("document.fonts.ready")`

## HTML 报告结构（`assets/report-template.html`）

```
1. NAV       FloatFu-true · 游资 SKILLS
2. HERO      股票名 + 价格 + 一句话定调 + O.o 雷达眼水印
3. SAFETY    🟢🟡🟠🔴 杀猪盘横幅
4. CORE      4 段 Dashboard（大众视图）⭐ 主视觉
            ├ core_conclusion
            ├ data_perspective (4 small cards)
            ├ intelligence
            └ battle_plan
5. DIVIDE    The Great Divide ⭐ 戏剧高潮
            左红 vs 右绿，像素头像对撞，3 轮辩论气泡，PUNCHLINE 大字
6. PANEL     50 贤评审团 (7 Tab 切换)
            每张卡片：像素头像 + score 环 + signal 灯 + comment + 展开
7. RADAR     19 维雷达图 + 折叠详情
8. RISKS     🔴 风险清单（红框）
9. ZONES     四派系买入区间对比
10. WAR      隐藏 #war-report (1920x1080)
11. CARD     隐藏 #share-card (1080x1920)
12. FOOTER   免责声明 + 数据时间戳
```

## 4 段 Dashboard 模板（大众视图，最重要）

```html
<section class="dashboard">
  <div class="card core">
    <h3>核心结论</h3>
    <p class="punchline">{{dashboard.core_conclusion}}</p>
  </div>
  <div class="grid-4">
    <div class="cell">📈 趋势 · {{trend}}</div>
    <div class="cell">💰 价位 · {{price}}</div>
    <div class="cell">📊 量能 · {{volume}}</div>
    <div class="cell">🎯 筹码 · {{chips}}</div>
  </div>
  <div class="grid-3">
    <div class="cell">📰 新闻 · {{news}}</div>
    <div class="cell">⚠️ 风险 · {{risks}}</div>
    <div class="cell">🚀 催化 · {{catalysts}}</div>
  </div>
  <div class="battle-plan">
    🎯 进场 {{entry}} · 仓位 {{position}} · 止损 {{stop}} · 目标 {{target}}
  </div>
</section>
```

## The Great Divide 模板

```html
<section id="great-divide">
  <h2>⚔️ THE GREAT DIVIDE · 世纪分歧</h2>
  <div class="divide-arena">
    <div class="bull-side">
      <img src="avatars/{{bull.id}}.svg" class="pixel-avatar bull">
      <div class="name">{{bull.name}}</div>
      <div class="score bullish">{{bull.score}}</div>
      <div class="bubble">{{bull.last_say}}</div>
    </div>
    <div class="vs">VS</div>
    <div class="bear-side">
      <img src="avatars/{{bear.id}}.svg" class="pixel-avatar bear">
      <div class="name">{{bear.name}}</div>
      <div class="score bearish">{{bear.score}}</div>
      <div class="bubble">{{bear.last_say}}</div>
    </div>
  </div>
  <div class="punchline-banner">
    💥 {{great_divide.punchline}}
  </div>
</section>
```

## 配色（Cinematic Sci-Fi）

```css
--bg-deep:    #0a0e17;
--bg-card:    #111827;
--border:     #1e2a3a;
--neon-cyan:  #06b6d4;
--neon-gold:  #f59e0b;
--bull-green: #10b981;
--bear-red:   #ef4444;
--text-main:  #e2e8f0;
--text-dim:   #64748b;
--accent-purple: #a78bfa;

font-family: 'JetBrains Mono', ui-monospace, monospace;
```

霓虹边光：`box-shadow: 0 0 20px rgba(6, 182, 212, 0.3), inset 0 0 20px rgba(6, 182, 212, 0.05);`

## one-liner.txt 模板

```
{{name}} 体检结果：{{score}} 分，{{verdict_short}}。
50 位大佬里 {{bullish}} 人喊买，{{best_investor}} {{best_score}} 分最看好。
风险：{{top_risk}}；亮点：{{top_strength}}。
{{trap_emoji}} {{trap_label}}。  全文 → reports/{{ticker}}_{{date}}/
```

## 完成检查

- [ ] 4 个产物文件全部生成
- [ ] HTML 在 Chrome 打开无 console error
- [ ] 截图 PNG 像素清晰（>1.5MB 说明 DPI 够）
- [ ] punchline 不在禁止清单里
- [ ] 风险清单至少 1 条带具体数字
- [ ] dashboard.core_conclusion 不超过 60 字

完成后向用户汇报：
```
✅ 报告已生成
📄 完整报告: reports/{ticker}_{date}/full-report.html
🖼️  社交战报: reports/{ticker}_{date}/share-card.png
💬 一句话: {one-liner 内容}
```
