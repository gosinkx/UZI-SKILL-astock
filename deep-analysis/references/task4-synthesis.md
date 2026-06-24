# Task 4 · 综合研判 + 多空辩论 + 叙事合成 (v2.0)

> **⚠️ v2.0 关键变化**：这是整个流水线里**最依赖 Claude 判断**的 Task。脚本的 `generate_synthesis()` 只给你一个 stub，**Claude 必须重写**关键字段。

读取 `dimensions.json` + `panel.json` + `raw_data.dimensions.20_valuation_models / 21_research_workflow / 22_deep_methods`，做**五件事**：

1. 算综合评分（脚本完成）
2. **机构建模三角验证**（DCF / Comps / LBO / IC Memo 交叉引用）— 🧠 你主导
3. **多空辩论** — 🧠 你主导，必须引用具体数字
4. **Great Divide 金句** — 🧠 你写，必须有冲突感
5. **四派系买入区间** — 🧠 你写，每个价位必须有计算逻辑

## 🧠 Step 0 · 读取机构建模结果（新增）

脚本会在 `raw_data.json` 里存入以下预计算结果，**你必须先读**：

```python
d20 = raw["dimensions"]["20_valuation_models"]["data"]
#   d20["dcf"]           — WACC + FCF + 敏感性表 + safety_margin
#   d20["comps"]         — 同行分位 + 隐含价
#   d20["lbo"]           — IRR + MOIC + verdict
#   d20["three_statement"] — 5 年预测
#   d20["summary"]       — 汇总指标

d21 = raw["dimensions"]["21_research_workflow"]["data"]
#   d21["initiating_coverage"] — 评级 + 目标价 + 投资论点 + 风险
#   d21["earnings_analysis"]   — 超预期检测
#   d21["catalyst_calendar"]   — 真实事件 + 未来日程
#   d21["thesis_tracker"]      — 5 条支柱完好率
#   d21["idea_screens"]        — 5 套 quant 命中情况

d22 = raw["dimensions"]["22_deep_methods"]["data"]
#   d22["ic_memo"]            — 投委会建议 + 三情景 + 风险缓解
#   d22["competitive_analysis"]— Porter + BCG
#   d22["dd_checklist"]       — 5 工作流 21 项
#   d22["value_creation_plan"]— EBITDA 桥
```

**Claude 的第一件事**：读这些字段，**审查默认假设对这只股是否合理**（详见 `task1.5-institutional-modeling.md`）。如果明显不合理（比如半导体股用 stage1=10%），重跑一次：

```python
from lib.fin_models import compute_dcf
adjusted = compute_dcf(features, assumptions={"stage1_growth": 0.22, "beta": 1.4})
# 写入 synthesis.adjusted_dcf
```

## Step 4.1 综合评分

```
基本面得分 = dimensions.fundamental_score          (0-100)
评审共识   = panel.panel_consensus                (0-100)
综合评分   = 基本面 × 0.6 + 共识 × 0.4
```

定调阈值：
```
≥85   值得重仓     "可以下手了"
70-84 可以蹲一蹲   "不错的标的"
55-69 观望优先     "再看看"
40-54 谨慎         "别上头"
<40   回避         "下一个"
```

## Step 4.2 多空辩论（核心戏剧性）

**自动选角**：
- Bull = panel.investors 中 `signal=bullish` 且 `confidence` 最高的那位
- Bear = panel.investors 中 `signal=bearish` 且 `confidence` 最高的那位
- 若 bear 列表为空，从 `neutral` 中找 confidence 最高的当 bear

**辩论结构**（3 轮，每轮各 1 段）：

```json
{
  "debate": {
    "bull": { "investor_id": "...", "name": "...", "avatar": "..." },
    "bear": { "investor_id": "...", "name": "...", "avatar": "..." },
    "rounds": [
      {
        "round": 1,
        "bull_say": "我看多的核心理由是 ROE 五年都在 18% 以上...",
        "bear_say": "ROE 是过去式，PE 已经 70 分位，下一份财报只要不超预期就崩..."
      },
      {
        "round": 2,
        "bull_say": "PE 高是因为业绩可见度在提升...",
        "bear_say": "可见度的代价是产能过剩，下游已经在砍单..."
      },
      {
        "round": 3,
        "bull_say": "短期波动不影响长逻辑...",
        "bear_say": "长逻辑是用钱赌的，赌输要五年才知道..."
      }
    ],
    "judge_verdict": "辩论后综合判断：bull 略占上风，但 bear 的产能过剩论据值得警惕。建议在 X 价位以下分批介入。",
    "punchline": "ROE 连续五年 >15%，但今天被游资当成了弃子。"
  }
}
```

**辩论的语言规则**（违反必须重写）：
- ❌ 禁止："基本面良好"、"前景广阔"、"值得关注"、"建议重视"
- ✅ 必须有具体数字 + 一个反预期的事实 + 戏剧动词
- ✅ 每段 ≤ 80 字
- ✅ 至少出现一次"但是"、"问题是"、"代价是"、"代价"

`punchline` 是最后进入分享卡 PNG 的金句，要求**朋友圈传播力**：
- 长度 20-30 字
- 必须有冲突感
- 数据 + 情绪 二选一以上
- 例如：
  - "ROE 连续五年 >15%，今天却被游资当成了弃子。"
  - "段永平给 92 分，但 K 线已经走完了 Stage 3。"
  - "50 个大佬 18 个看多，最看好的那个明天就要解禁。"

## Step 4.3 风险清单

取 dimensions 中 score ≤ 4 的全部维度，按 `score × weight` 升序排，前 5 条进风险清单。每条 ≤ 30 字。

## Step 4.4 买入区间（v2.0 · 必须引用具体模型）

四派系各报一个理想价，每个价位**必须附计算逻辑**（不能只写"基于技术面"）：

```json
{
  "buy_zones": {
    "value":     { "price": 17.60, "rationale": "DCF 内在价 ¥20.73 × 0.85 安全边际" },
    "growth":    { "price": 18.50, "rationale": "Y3 EPS 0.95 × 同行中位 PE 19.5x" },
    "technical": { "price": 18.00, "rationale": "60 日均线支撑 + Stage 2 起涨点" },
    "youzi":     { "price": 18.56, "rationale": "龙虎榜近 3 次净买入集中区间" }
  }
}
```

**价值派优先从 DCF 拿**：`dcf.intrinsic_per_share × 0.85`
**成长派优先从 3-stmt 拿**：`three_statement.income_statement.net_income[2] / shares × 同行中位 PE`
**技术派**：60 日均线 / Stage 2 起涨点 / 颈线支撑
**游资派**：龙虎榜净买入集中区间 或 当前价（若仍在射程内）

## Step 4.5 机构建模三角验证（v2.0 · 新增）

把 DCF / Comps / LBO / IC Memo 并排展示，**突出冲突**：

```json
{
  "institutional_triangulation": {
    "dcf":       { "intrinsic": 20.73, "safety_margin": -28.6, "verdict": "🟠 略微高估" },
    "comps":     { "pe_percentile": 0, "implied_via_pe": 59.98, "verdict": "🟢 便宜（PE 低于 75% 同行）" },
    "lbo":       { "irr_pct": 21.7, "verdict": "🟢 PE 买方可赚 20%+ IRR" },
    "ic_memo":   { "recommendation": "⚪ 观望 (HOLD)" },
    "conflict_note": "DCF 说高估 28%，但 LBO 说 PE 买方仍赚 21% IRR，Comps 也显示同行中最便宜 — 冲突主要来自 DCF 的 WACC 过高还是成长假设过低？需要重审 stage1 增速假设。"
  }
}
```

**Claude 必须写 `conflict_note`**，内容为"为什么三种方法结论不一致"的一句话解读。没有冲突时写"三种方法一致指向 X"。

## synthesis.json 完整结构

```json
{
  "ticker": "002273.SZ",
  "name": "水晶光电",
  "overall_score": 78.4,
  "verdict_label": "可以蹲一蹲",
  "verdict_short": "不错的标的",
  "fundamental_score": 76.0,
  "panel_consensus": 82.0,
  "debate": { ... },
  "great_divide": {
    "bull_avatar": "buffett",
    "bear_avatar": "burry",
    "bull_score": 92,
    "bear_score": 18,
    "punchline": "..."
  },
  "risks": ["商誉占净资产 35%", "..."],
  "buy_zones": { ... },
  "dashboard": {
    "core_conclusion": "78 分，可以蹲一蹲。50 位大佬里 24 人看多，最看好的是段永平 92 分。",
    "data_perspective": {
      "trend":   "Stage 2 初期，20 日均线刚翻多",
      "price":   "现价 18.56，距压力位还有 8%",
      "volume":  "近 5 日温和放量",
      "chips":   "股东户数连续 3 季下降"
    },
    "intelligence": {
      "news":     "iPhone 17 备货传闻 + AR 眼镜 BOM 渗透",
      "risks":    ["商誉 35%", "PE 历史 70 分位"],
      "catalysts":["6 月新品发布", "Q2 业绩预告"]
    },
    "battle_plan": {
      "entry":    "16.20-17.00 分批",
      "position": "标准仓 50% 起步，破 16 加到 80%",
      "stop":     "破 15.50 离场",
      "target":   "短线 22，中线 28"
    }
  }
}
```

完成后向用户汇报：`Task 4 ✓ 综合 X 分 + 辩论金句 "..."`。
