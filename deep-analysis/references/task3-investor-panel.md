# Task 3 · 50 贤评审团

加载 `investor-panel` skill 让 50 位投资大佬各自按方法论给出 Signal。

## Pydantic Signal 模式（抄自 ai-hedge-fund）

每位投资者必须输出严格三元组：
```json
{
  "investor_id": "buffett",
  "name": "巴菲特",
  "group": "A",
  "signal": "bullish",          // bullish | bearish | neutral
  "confidence": 87,             // 0-100，越高越坚定
  "score": 82,                  // 0-100，综合评分（沿用原方案，便于排序）
  "verdict": "买入",            // 强烈买入/买入/关注/观望/等待/回避/不达标/不适合
  "reasoning": "ROE 五年>18%，护城河清晰，但价格已经不便宜，等回调...",
  "comment": "用该投资者语言风格的金句，1-2 句",
  "pass": ["ROE>15% 连续 5 年", "净利率 22%"],
  "fail": ["PE 已超历史 70 分位"],
  "ideal_price": 16.20,         // 理想买入价（如适用）
  "period": "3-5 年"            // 建议持仓周期
}
```

## 7 大流派分组

| 组 | 名称 | 人数 | references |
|---|---|---|---|
| A | 经典价值派 | 6 | `group-a-classic-value.md` |
| B | 成长投资派 | 4 | `group-b-growth.md` |
| C | 宏观对冲派 | 5 | `group-c-macro-hedge.md` |
| D | 技术趋势派 | 4 | `group-d-technical.md` |
| E | 中国价投/公募派 | 6 | `group-e-china-value.md` |
| F | A 股游资派 | 22 | `group-f-china-youzi.md` |
| G | 量化系统派 | 3 | `group-g-quant.md` |
| **共** | | **50** | |

> 22 位游资 = 17 经典 + 2025 新增 5 位（六一中路、交易猿、流沙河、古北路、北京炒家）。

## 字段白名单（per-persona 抄 ai-hedge-fund）

每位投资者只看自己关心的维度，避免噪音：

```python
FIELD_WHITELIST = {
  "buffett":   ["1_financials", "10_valuation", "11_governance", "14_moat"],
  "graham":    ["1_financials", "10_valuation"],
  "lynch":     ["1_financials", "7_industry", "10_valuation"],
  "minervini": ["2_kline", "16_lhb"],
  "youzi.*":   ["2_kline", "12_capital_flow", "15_events", "16_lhb", "17_sentiment"],
  "trap":      ["18_trap"],
  ...
}
```

游资统一不看财报（除小鳄鱼），只看 K线+资金+龙虎榜+情绪。

## 执行流程

1. 加载 `assets/investor-cards.json`（50 人元数据）
2. 对每位投资者：
   a. 取出该 persona 的字段白名单
   b. 从 `dimensions.json` + `raw_data.json` 提取相关字段
   c. 调用 LLM（即 Claude 自己），用该 persona 的方法论 + 语言样本生成 Signal
   d. 强制 JSON 输出
3. 汇总到 `panel.json`：
```json
{
  "ticker": "002273.SZ",
  "panel_consensus": 64.2,         // 看多人数 / 50 × 100
  "vote_distribution": {
    "strongly_buy": 8, "buy": 12, "watch": 18, "wait": 7, "avoid": 3, "n_a": 2
  },
  "signal_distribution": {
    "bullish": 24, "neutral": 17, "bearish": 9
  },
  "investors": [ {Signal}, {Signal}, ... ]   // 50 个
}
```

## 重要：游资是否在射程内

22 位游资，**不是每只票都适合每位游资**。判断规则：

| 游资 | 适合的票 | 不适合则 |
|---|---|---|
| 章盟主 | 市值 > 200 亿 + 趋势向上 | `signal: neutral, verdict: 不适合` |
| 赵老哥 | 板块辨识度龙头 + 连板潜力 | 同上 |
| 佛山无影脚 | 小盘 + 超跌 | 同上 |
| 北京炒家 | 20-80 亿 + 题材 + 机构持仓 < 10% | 同上 |
| ... | （详见 group-f-china-youzi.md） | |

不适合的票，verdict 写 "不适合"，confidence 仍要给（基于"不在射程内"的确定性）。

完成后向用户汇报：`Task 3 ✓ 50 位评审完成，看多 X / 中性 Y / 看空 Z`。
