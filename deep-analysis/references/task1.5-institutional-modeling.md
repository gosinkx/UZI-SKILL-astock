# Task 1.5 · 机构级建模细则

> 改编自 anthropics/financial-services-plugins，A 股 / 港股 / 美股适配。

Task 1.5 在 Task 1 采集完原始数据后自动执行，计算 3 个新维度（dim 20 / 21 / 22），共涉及 17 种机构级分析方法。脚本部分位于 `scripts/compute_deep_methods.py`，底层 lib 在 `scripts/lib/fin_models.py`、`scripts/lib/research_workflow.py`、`scripts/lib/deep_analysis_methods.py`。

## 默认假设（A 股适配）

| 参数 | 默认 | 理由 |
|---|---|---|
| 无风险利率 rf | 2.5% | 10Y 中国国债收益率 |
| 股权风险溢价 ERP | 6.0% | A 股历史 |
| Beta | 1.0 | 市场中性 |
| 目标债务比例 | 30% | A 股中位 |
| 税前债务成本 | 4.5% | LPR + 0.5-1pp |
| 标准税率 | 25% | 企业所得税 |
| 高新税率 | 15% | 认定企业 |
| Stage 1 增速 | 10% | 5 年高增长期 |
| Stage 2 增速 | 5% | 5 年过渡期 |
| 终值永续 g | 2.5% | 长期名义 GDP |

## Claude 的假设审查职责

**脚本用的是保守默认值**。你作为分析师必须根据公司特性判断是否需要调整：

### 行业 × 假设调整规则（推荐值）

| 行业类型 | stage1 growth | beta | terminal g | 原因 |
|---|---|---|---|---|
| 半导体 / 光学 / AI 硬件 | 15-25% | 1.3-1.5 | 3% | 周期 + 高成长 |
| 消费白马 (茅、五粮液类) | 8-12% | 0.8-0.9 | 3% | 稳定现金流 |
| 创新药 | 15-30% | 1.5-2.0 | 2% | 高风险高回报 |
| 银行 / 保险 | 3-5% | 0.8-1.0 | 2% | 成熟行业 |
| 煤炭 / 钢铁 / 化工 | -5% 到 +5% | 1.2-1.5 | 1.5% | 周期性强 |
| 互联网平台 | 12-18% | 1.2 | 3% | 取决于垂类 |
| 新能源车 / 锂电 | 20-40% | 1.5-1.8 | 3% | 高速成长期 |
| 传统制造业 | 5-8% | 1.0 | 2% | 稳定低增 |
| ST / 困境反转 | 视管理层 | 1.5 | 2% | 高度不确定 |

### 何时必须覆盖默认值

1. **行业增速与默认 10% 明显偏离** — 跑 `compute_dcf` 时传 `assumptions={"stage1_growth": ...}`
2. **公司历史 3 年增速远高/低于默认** — 用历史 CAGR 重算
3. **高新资质** — `tax=0.15`
4. **重资产 / 高杠杆** — `target_debt_ratio=0.50`
5. **负债极低** — `target_debt_ratio=0.10`

### 示例覆盖写法

```python
from lib.fin_models import compute_dcf

# 半导体高成长
dcf = compute_dcf(features, assumptions={
    "stage1_growth": 0.22,
    "stage2_growth": 0.12,
    "terminal_g": 0.03,
    "beta": 1.4,
    "tax": 0.15,
})

# 把调整后的结果覆盖回 synthesis.json
# synthesis["adjusted_dcf"] = dcf
```

### 在报告里呈现分歧

如果默认 DCF 说 "高估 28%" 但调整后说 "低估 15%"，**两个结果都写出来**：

```
📊 DCF 估值分歧
  默认假设（stage1 10%, beta 1.0）: ¥20.73 · -28.6% (高估)
  行业调整（stage1 22%, beta 1.4） : ¥34.50 · +18.8% (低估)
  🔍 分歧点: 市场对光学行业增速的假设差异
```

## 敏感性表阅读

compute_dcf 返回的 `sensitivity_table` 是一个 5×5 矩阵：
- 行 = WACC (±200bp around center)
- 列 = terminal g (±100bp around center)
- **中心格必须等于基础案例的每股内在价值**（自检机制）

在报告里展示时，用热力图配色：
- 中心 ≥ 1.3× 当前价 → 深绿
- 中心 ≥ 1.1× 当前价 → 浅绿
- 中心 ≈ 当前价 → 灰
- 中心 ≤ 0.9× 当前价 → 浅红
- 中心 ≤ 0.7× 当前价 → 深红

## LBO 交叉验证

`quick_lbo` 是"PE 基金买方视角"的第二意见：
- 如果 LBO IRR ≥ 20% → 🟢 PE 基金今天愿意买
- 如果 15-20% → 🟡 边际，不太会买
- 如果 < 15% → 🔴 PE 基金会放弃

**这是对 DCF 的独立交叉校验**。如果 DCF 说高估但 LBO 说 IRR 还有 21%，那通常是 DCF 的折现率设得太高或增长假设太低。

## Comps 缺失时的处理

同行数据经常因为 web fetch 失败为空。如果 `build_comps_table` 返回 `error: no peers provided`：
1. 手动调用 `fetch_similar_stocks.py {ticker}` 单独重跑
2. 或手写 3-5 家主要竞争对手的 `{name, pe, pb, roe, ...}` 传进去
3. 报告里**明确标注** "同行数据不足，Comps 估值缺失"

## 叙事引用方式

在 Task 4 的 synthesis 里，你引用机构建模结果的标准格式：

```markdown
📐 机构级建模三角验证：
  • DCF:  ¥{dcf.intrinsic_per_share} · {dcf.safety_margin_pct}% · {dcf.verdict}
  • Comps: {comps.valuation_verdict} (PE 分位 {comps.target_percentile.pe}%)
  • LBO:  IRR {lbo.irr_pct}% · {lbo.verdict}

🏛️ 首次覆盖：{initiating.rating} · 目标价 ¥{target_price} ({upside_pct}%)
📋 IC Memo 结论: {ic_memo.recommendation}
⚔️ Porter: 行业吸引力 {competitive.industry_attractiveness}% · BCG {bcg_position}
```

永远引用数字，永远标注 dim 来源（dim 20/21/22）。
