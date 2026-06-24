# Task 2.5 · 6 维定性深度分析方法论（v2.4）

> 本文档是 [SKILL.md · HARD-GATE-QUALITATIVE](../SKILL.md) 的详细操作手册。
> 覆盖 6 个"纯爬虫搞不定"的维度，要求 agent 做高强度跨域联想 + 多 agent 并行抓取。

---

## 0. 为什么需要这份文档

UZI-Skill 的 22 个维度里，有 6 个维度**爬虫只能拿到原始片段，无法产出有洞察的结论**：

| 维度 | 爬虫产出 | 缺失的关键判断 |
|---|---|---|
| 3 · 宏观环境 | 利率/汇率/地缘/大宗的**新闻片段** | 这些宏观变量**如何具体传导到这只股**？ |
| 7 · 行业景气 | 行业 PE 中位数、默认 TAM | 赛道在生命周期哪个阶段？谁是 winner？ |
| 8 · 原材料 | 近 12 月大宗价格曲线 | 涨价能否顺价？毛利率弹性多少？ |
| 9 · 期货关联 | 关联品种近 60 日走势 | 套保敞口多少？contango 暗示什么库存策略？ |
| 13 · 政策与监管 | 政策搜索片段 | 这条政策对公司**具体业务**的影响？受益者是龙头还是新玩家？ |
| 15 · 事件驱动 | 近期公告列表 | 每条事件的**货币化影响**？子公司业务的独立价值？并购意图？ |

**关键观察**：这些维度的真正价值在于**连接**——把孤立片段连成因果链。纯爬虫给不了因果。

## 示例 · 三条孤立数据如何连成一个论点

```
事件驱动：子公司中标 20 亿基建工程      ← raw 片段
政策与监管：地方财政预算下修 15%          ← raw 片段
原材料：钢铁期货近月上涨 8%               ← raw 片段
────────────────────────────────────────
agent 的因果链（这才是"分析"）：
  "20 亿中标 → 但甲方是地方财政吃紧的城投公司 → 应收账款账期拉长
   + 原材料涨 8% 又压缩毛利 → 这单工程看起来是利好、实际是拿利润换周转"
```

**这种连接必须由 agent 完成，脚本做不到。**

---

## 1. 多 Agent 分工（强制 PARALLEL 执行）

完成这 6 维必须 spawn **3 个并行 sub-agent**，每 agent 负责 2 个强关联维度。禁止用 1 个
agent 串行覆盖 6 维（串行跑至少 3×更慢，且容易漏掉跨域思考）。

### 分组标准 · 强关联维度配对

| Sub-agent | 维度 | 核心主轴 | 关键联想 |
|---|---|---|---|
| **A · Macro-Policy** | 3_macro + 13_policy | 宏观政策耦合 | 美联储 → 汇率 → 出口业务<br/>国家战略 → 行业补贴 → 公司能拿几成<br/>反垄断/环保 → 子公司业务被卡 |
| **B · Industry-Events** | 7_industry + 15_events | 行业结构 + 公司动态 | 行业集中度拐点 → 龙头份额<br/>子公司合同 → 营收增厚测算<br/>并购新闻 → 整合者 vs 被整合<br/>研发进展 → 3-5 年估值跳跃 |
| **C · Cost-Transmission** | 8_materials + 9_futures | 成本传导链 | 上游原材料涨价 → 毛利率弹性<br/>国产替代 → 采购成本长期下行<br/>期货 contango/backward → 备货策略<br/>套保敞口 → 财报意外 |

### Sub-agent 启动模板（直接复制，主 agent 在 stage1 之后用 Agent tool 启动）

**Sub-agent A · Macro-Policy Prompt**:
```
你要扮演一位擅长宏观研究 + 政策分析的首席策略师，深度分析这只股票的
宏观环境（dim 3）和政策与监管（dim 13）维度。

公司：{name} ({ticker})
行业：{industry}
主营业务：{main_business}
子公司/投资版图：{subsidiaries_from_10K}

原始数据位置：
  - .cache/{ticker}/raw_data.json · dimensions["3_macro"]
  - .cache/{ticker}/raw_data.json · dimensions["13_policy"]

你必须回答的问题清单见 task2.5 第 2 节 Dim 3 和 Dim 13 的小节。

强制动作：
1. 用 WebSearch 搜 "2026 {industry} 国家政策"、"2026 {industry} 监管变化"
2. 用 Chrome/Playwright MCP 打开以下 URL 抓取最新政策原文：
   - https://www.gov.cn/zhengce/   (国务院)
   - http://www.csrc.gov.cn/csrc/c106187/common_list.shtml  (证监会)
   - https://www.miit.gov.cn/   (工信部，制造业相关)
3. 至少给出 2 条【宏观 ↔ 政策】交叉因果链（任选 task2.5 第 3 节的 6 条之一）
4. 评估政策的受益者：是龙头（市场化分配）还是新玩家（补贴扶持）？本股处于什么位置？

输出必须严格按照 task2.5 第 5 节 schema，写到 agent_analysis.json 的
qualitative_deep_dive["3_macro"] 和 ["13_policy"] 字段。每条 finding 必须带 url 引用。
```

**Sub-agent B · Industry-Events Prompt**:
```
你要扮演一位资深行业研究员 + 公司事件追踪师，深度分析这只股票的
行业景气（dim 7）和事件驱动（dim 15）维度。

公司：{name} ({ticker})
行业：{industry}
市值：{market_cap}
最近 60 天公告数：{len(recent_news)}

原始数据位置：
  - .cache/{ticker}/raw_data.json · dimensions["7_industry"]
  - .cache/{ticker}/raw_data.json · dimensions["15_events"]

你必须回答的问题清单见 task2.5 第 2 节 Dim 7 和 Dim 15 的小节。

强制动作：
1. WebSearch："{name} 子公司 业务"、"{name} 并购 2026"、"{industry} 市场份额排名"
2. 用 Chrome/Playwright MCP 打开：
   - http://www.cninfo.com.cn/new/disclosure/stock?stockCode={code_raw}  (巨潮公告原文)
   - https://xueqiu.com/S/{code_raw}/announcements  (雪球公告)
   - https://xueqiu.com/S/{code_raw}/F10/industry  (雪球行业信息)
3. 列出过去 90 天内公司/子公司的**所有重要事件**并做货币化影响估算
4. 至少验证 1 条【行业 ↔ 事件】因果链（例如：行业集中度上升 → 龙头并购 → 本股是
   收购方还是被收购方？）
5. 若有子公司独立业务 → 做一次分部估值（SOTP），告诉我子公司如果独立上市值多少

输出写入 qualitative_deep_dive["7_industry"] 和 ["15_events"]。
```

**Sub-agent C · Cost-Transmission Prompt**:
```
你要扮演一位成本分析专家 + 期货分析师，深度分析这只股票的
原材料（dim 8）和期货关联（dim 9）维度。

公司：{name} ({ticker})
行业：{industry}
历史毛利率：{gross_margin_history}

原始数据位置：
  - .cache/{ticker}/raw_data.json · dimensions["8_materials"]
  - .cache/{ticker}/raw_data.json · dimensions["9_futures"]

你必须回答的问题清单见 task2.5 第 2 节 Dim 8 和 Dim 9 的小节。

强制动作：
1. WebSearch："{name} 原材料 成本占比"、"{name} 套期保值 年报"、"{name} 国产替代"
2. 用 Chrome/Playwright MCP 打开：
   - https://data.eastmoney.com/futures/index.html
   - https://www.shfe.com.cn/data/dailydata/   (上期所)
3. **必做**：毛利率敏感性分析 —
   假设核心原材料价格 +10% / +20% / -10% / -20%，毛利率相应变动多少？
4. 从公司年报披露的"金融衍生品"段落判断套保敞口（买入 vs 卖出，名义本金）
5. 至少验证 1 条【大宗 ↔ 期货】因果链

输出写入 qualitative_deep_dive["8_materials"] 和 ["9_futures"]。
```

---

## 2. 每维度的必答问题清单

agent **必须逐条回答** — 回答不能是"不清楚"或"待查"。若找不到数据：
- 先走 browser MCP / WebSearch
- 再不行 → 在 `qualitative_deep_dive[dim].evidence` 里标 `{"source": "unknown", "finding": "该字段无公开数据"}`
- 绝不留空 / 不写废话（"值得关注" / "需要观察"）

### Dim 3 · 宏观环境（5 问）
1. **利率周期**：当前处于加息 / 降息 / 平台期？对公司资金成本和 DCF 估值的影响是正是负？量化：每 +25bp 影响几个点 ROE
2. **汇率敞口**：公司出口占营收多少？进口原料占成本多少？当前人民币趋势的净影响？
3. **地缘政策**：关税 / 制裁 / 出口管制是否命中公司产品？列出具体产品线和目的地国家
4. **大宗商品**：把 dim 8（原材料）和 dim 9（期货）的数据**引用进来**，不要重复描述，直接说宏观因素对它们的传导
5. **需求指标**：当前 M2/社融/PMI 读数暗示下游需求的扩张还是收缩？与公司所在行业的历史相关性？

### Dim 7 · 行业景气（7 问）
1. **生命周期**：导入期 / 成长期 / 成熟期 / 衰退期？依据（历史 CAGR、渗透率、替代率）
2. **TAM & 增速**：3 年预测 TAM 是多少亿？信达 / 中金 / 券商研报的分歧区间？
3. **集中度变化**：过去 3 年 CR4 / CR8 变化（龙头在收割 or 分散）
4. **波特五力速评**：上下游议价 / 替代品 / 进入壁垒 / 行业内竞争 · 每个打 1-5 分并解释
5. **替代品风险**：是否有颠覆性技术（如 AI vs 传统 SaaS、新能源 vs 燃油车）威胁赛道？
6. **公司地位**：本股在行业里排第几？龙头 / 追赶者 / 尾部？市占率数字
7. **M&A 活跃度**：行业近 6 个月有无重大并购？本公司是整合者还是被整合对象？

### Dim 8 · 原材料（5 问）
1. **成本构成**：核心原材料占营业成本多少比例？引用年报或券商"成本拆解"章节
2. **价格走势**：引用 dim 8 的 `price_history_12m`，指出当前处于过去 3 年百分位几？
3. **顺价能力**（最关键）：原料涨 10% → 毛利率变化多少？测算逻辑：
   - 如果合同定价机制 = 成本加成 → 基本能顺价
   - 如果合同 = 固定价 → 压毛利
   - 提供 3 档情景（+10% / +20% / +30%）下的毛利率
4. **替代 / 长协**：是否有国产替代方案进行中？是否签了长单锁定原料价？
5. **向上游一体化**：子公司是否涉及原料端（如电池厂做锂矿）？长期成本优势

### Dim 9 · 期货关联（4 问）
1. **Lead-lag 关系**：关联期货与公司股价的时滞关系（通常期货领先 1-3 个月）
2. **套保敞口**：公司年报"金融衍生品"章节披露的名义本金多少？多头 / 空头？
3. **Contango vs Backwardation**：当前曲线形态暗示什么库存策略？
4. **异常持仓**：关联品种近期持仓异常变化对公司经营的影响？

### Dim 13 · 政策与监管（6 问）
1. **国家战略对齐度**：十五五规划 / 制造强国 / 双碳 / 数字经济 / 专精特新 — 公司符合哪几条？
2. **近 6 个月新政策**：针对公司行业的新政策（补贴 / 税收 / 环保 / 安全 / 反垄断 / 出口管制）— 列出每一条的**原文摘录**和发文机构
3. **受益者判断**（关键）：这条政策受益者是行业龙头还是新进入者？公司处于什么位置？
4. **地方财政**：特别是基建 / 城投 / 公用事业类——地方财政压力如何传导到本公司？
5. **资质与税率**：是否在高新技术认证 / 专精特新 / "小巨人"名单？税率优惠？
6. **海外监管**：FDA / SEC / 欧盟 / 美国商务部实体清单等对出海业务的影响？

### Dim 15 · 事件驱动（6 问）
1. **近 30 天公告分类**：按"合同中标 / 研发进展 / 股东变动 / 诉讼 / 并购 / 业绩预告 / 其他"归类，给每类做计数和总金额
2. **每条事件的货币化**：合同金额占营收多少 %？研发费用占营收？诉讼涉及金额？
3. **催化剂日历**（未来 60 天）：年报 / 季报 / 业绩说明会 / 股东大会 / 限售解禁日期
4. **子公司独立价值**（SOTP）：核心子公司如果独立上市，按同行 PE / PS 估值几何？与当前市值的比较
5. **并购影响**（如有）：被并购方 / 并购方？交易对价？EPS 增厚或摊薄的一阶估算
6. **监管调查 / 诉讼**：金额量级 + 判决概率（引用相似案例）

---

## 3. 跨域因果链 · agent 至少验证 3 条

这 6 条是 UZI-Skill 总结的"最有信息量"的因果链。agent 在这 6 条里**挑至少 3 条**进行验证，
结果写入 `qualitative_deep_dive[dim].associations[]`。

### 链 1 · 宏观 → 原材料 → 毛利率
```
利率下行 → 大宗回调 → 公司原料成本 ↓ → 毛利率 ↑
(关键问题：这只股对原料的毛利弹性是多少？dim 8 的敏感性表告诉你)
```

### 链 2 · 政策 → 行业 → 份额重分配
```
新政策发布（补贴 / 许可证 / 准入门槛）→ 强化 TAM 或压制旧玩家 →
行业集中度变化 → 本公司份额上升 or 下降？
(关键问题：政策的受益者是龙头还是新玩家？)
```

### 链 3 · 事件 → 估值跳跃
```
子公司中标大合同 / 重大研发突破 / 并购新业务 → 营收或利润分部估值 ↑↑ →
DCF 和 SOTP 分歧 → 买入机会或假突破？
```

### 链 4 · 期货 → 财报
```
公司套保敞口（多 or 空）× 期货价格波动 → 财务报表非经常性损益 →
下个季度利润 beat / miss
```

### 链 5 · 宏观 → 地方 → 公司
```
顶层宏观压力（利率高 / 房地产压制）→ 地方财政紧 → 城投付款慢 →
工程类公司应收账款飙升 → 现金流恶化
(特别适合：基建 / 园林 / 市政 / 公用事业)
```

### 链 6 · 行业整合 → 公司定位
```
并购活跃期 → 小公司被收购 + 龙头份额上升 →
本股是整合者（上车）还是下一个被整合（套利）？
(关键问题：估值是否已 price in 并购预期？)
```

---

## 4. Browser/MCP 抓取 URL 模板

直接复制到 sub-agent prompt 里让它用 Chrome/Playwright MCP 打开。
**注意**：`push2.eastmoney.com` 和 `82.push2.eastmoney.com` 2026 年经常被反爬，优先用下面
列出的可用域。

> **完整源清单见 `lib/data_source_registry.py`**。Agent 可在 sub-agent 里直接 import：
> ```python
> from lib.data_source_registry import http_sources_for, playwright_sources_for
> primary = http_sources_for("4_peers", "A")          # tier-1 HTTP 源
> browser_only = playwright_sources_for("4_peers", "A")  # tier-2 浏览器源（雪球/问财/同花顺 F10）
> ```
> 用注册表的好处：每个源带 `health` 标记 ("known_good"/"flaky"/"blocked_often"/"needs_browser")，agent 自己挑。

### Dim 3 · 宏观（v2.5 扩充）
```
https://data.eastmoney.com/hsgt/board.html         (北向/南向资金面板)
https://data.eastmoney.com/hgt/zb.html             (汇率)
https://data.eastmoney.com/cjsj/pmi.html           (PMI)
https://data.eastmoney.com/cjsj/cpi.html           (CPI)
https://www.chinamoney.com.cn/chinese/             (中债)
https://wallstreetcn.com/                          (华尔街见闻 · 海外联动 + 快讯)
https://www.yicai.com/                             (第一财经 · 宏观与产业专题)
https://www.investing.com/economic-calendar/       (Investing 经济日历 · 海外宏观)
https://www.investing.com/commodities/             (Investing 商品 · 大宗联动)
```

### Dim 4 · 同行（v2.5 新加 · A 股原 fetcher 已有，agent 可补充非 A 股或需 NLP 筛选场景）
```
A 股：
https://www.iwencai.com/                           (问财 NLP · 需 Playwright；'同行业 市值>100亿' 类查询)
https://stockpage.10jqka.com.cn/                   (同花顺 F10 · 需 Playwright；行业/概念板块 + 同行)

港股：
https://www.aastocks.com/sc/stocks/analysis/industry/  (AASTOCKS · 港股按行业列表 · 需 Playwright)
```

### Dim 7 · 行业（v2.5 扩充）
```
https://xueqiu.com/S/{code}/F10/industry           (雪球 F10 行业信息 · 需 Playwright)
https://data.eastmoney.com/bkzj/                   (板块资金)
https://www.iresearch.com.cn/                      (艾瑞 · 互联网行业)
https://www.iwencai.com/                           (问财 · NLP 筛选行业内成员)
https://stockpage.10jqka.com.cn/                   (同花顺 F10 · 行业景气度)
```

### Dim 8/9 · 大宗 & 期货
```
https://data.eastmoney.com/futures/index.html     (期货总览)
https://www.shfe.com.cn/data/dailydata/           (上期所日报)
https://www.dce.com.cn/                           (大商所)
https://www.czce.com.cn/                          (郑商所)
https://www.100ppi.com/                           (生意社 · 现货)
https://www.investing.com/commodities/            (海外大宗联动)
```

### Dim 13 · 政策（v2.5 扩充）
```
https://www.gov.cn/zhengce/                                  (国务院政策)
http://www.csrc.gov.cn/csrc/c106187/common_list.shtml        (证监会监管动态)
https://www.miit.gov.cn/                                     (工信部)
https://www.ndrc.gov.cn/xxgk/jd/                             (发改委政策解读)
https://www.samr.gov.cn/                                     (市场监管总局 · 反垄断)
https://www.cls.cn/                                          (财联社 7x24 · 政策电报第一时间)
https://wallstreetcn.com/                                    (华尔街见闻 · 海外政策 + 国际反应)
```

### Dim 15 · 事件（v2.5 扩充）
```
A 股：
http://www.cninfo.com.cn/new/disclosure/stock?stockCode={code_raw}  (巨潮 · 公告法定原文)
https://xueqiu.com/S/{code_raw}/announcements                       (雪球公告聚合)
http://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllBulletin/stockid/{code_raw}.phtml  (新浪)
https://www.cls.cn/                                                  (财联社 7x24 · 突发事件最快)
https://www.yicai.com/                                               (第一财经 · 公司频道)
https://stock.jrj.com.cn/                                            (金融界 · 题材联动)
https://money.163.com/                                               (网易财经 · 新闻聚合)

港股：
https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=zh&stockId={int_code}  (HKEXNews · 法定披露)
https://www.aastocks.com/sc/cnhk/news/company-news/{code}.html                (AASTOCKS 港股新闻)
```

### Dim 16 · 龙虎榜（v2.5 新加）
```
https://data.eastmoney.com/stock/lhb.html          (东财龙虎榜)
https://www.yuncaijing.com/data/lhb/main.html      (云财经龙虎榜 · 游资席位 + 题材热度)
```

---

## 5. 输出 Schema · 写回 agent_analysis.json

6 个定性维度的分析全部写入 `.cache/{ticker}/agent_analysis.json` 的
`qualitative_deep_dive` 字段（v2.4 新增）。结构严格约束：

```json
{
  "agent_reviewed": true,
  "dim_commentary": { "3_macro": "...", ... },
  "panel_insights": "...",
  "qualitative_deep_dive": {
    "3_macro": {
      "evidence": [
        {
          "source": "国务院.gov.cn | cninfo | xueqiu | websearch | browser | mx_api | annual_report",
          "url": "https://www.gov.cn/zhengce/xxx.html",
          "finding": "人民币兑美元 2026-04 中间价较年初贬值 2.1%；公司出口占营收 45%",
          "retrieved_at": "2026-04-17"
        }
      ],
      "associations": [
        {
          "link_to": "8_materials",
          "chain_id": "链 1",
          "causal_chain": "美联储加息 → 人民币贬值 → 公司进口铜原料成本 +3% → 毛利率 -1.2pp",
          "estimated_impact": "影响 EPS 约 -0.08元"
        }
      ],
      "conclusion": "宏观中性偏利空，主要拖累来自进口成本上行和出口议价弱化"
    },
    "7_industry": { ... },
    "8_materials": { ... },
    "9_futures": { ... },
    "13_policy": { ... },
    "15_events": { ... }
  },
  "great_divide_override": { ... },
  "narrative_override": { ... }
}
```

### 字段约束

| 字段 | 类型 | 约束 |
|---|---|---|
| `evidence[]` | list[obj] | 每维 ≥ 2 条，每条必有 `url`（允许 `"source": "unknown"` 但必须说明） |
| `associations[]` | list[obj] | 6 维合计 ≥ 3 条（对应第 3 节 6 条链中至少 3 条） |
| `conclusion` | string | 1-2 句，必须引用 evidence 和/或 associations，禁止空泛话术 |
| `dim_commentary[key]` | string | 必须 cite `qualitative_deep_dive[key].evidence[*].url` 中至少一条 |

### 质量红线（违反即视为未完成）
- ❌ evidence 为空、或 url 全部空字符串
- ❌ associations 全部是 "宏观影响公司" 这种无具体量化的泛泛而谈
- ❌ conclusion 出现"值得关注 / 需要观察 / 基本面良好"三词之一
- ❌ 6 维 dim_commentary 复制 raw_data 的原始片段

---

## 6. 与现有 HARD-GATE 的关系

- **HARD-GATE-NAME**（v2.3）：名字解析失败 → 早退
- **HARD-GATE-DATAGAPS**（v2.3）：数据字段缺失 → agent 用浏览器补齐
- **HARD-GATE-QUALITATIVE**（v2.4，本文档）：定性维度空洞 → agent 深度分析

三个 gate 顺序执行：名字必须先解析对、数据尽量补全、再做定性深度分析。
`stage2()` 读到 `qualitative_deep_dive` 缺失会打印黄色警示（不 abort，遵循 v2.3 的
"agent 接管"原则）。

---

## 7. Performance 注意

- 3 个 sub-agent 并行，每个跑 5-10 分钟（含 WebSearch + browser 抓取）
- 总耗时 ≈ max(A, B, C) ≈ 10 分钟（vs 串行 30 分钟）
- 确保 sub-agent 使用 Agent tool `subagent_type=general-purpose` 真并行启动
- 不要让 sub-agent 之间等待彼此结果 — 完全独立

---

## 8. 例子 · 完整一条 evidence + association 的样子

以"宁德时代"为例：

```json
"qualitative_deep_dive": {
  "13_policy": {
    "evidence": [
      {
        "source": "工信部",
        "url": "https://www.miit.gov.cn/xwdt/gxdt/sjdt/art/2026/art_xxx.html",
        "finding": "《2026 新能源汽车推广方案》明确补贴向 300Wh/kg 以上电芯倾斜，公司 Kirin 4.0 已达标",
        "retrieved_at": "2026-04-17"
      }
    ],
    "associations": [
      {
        "link_to": "7_industry",
        "chain_id": "链 2",
        "causal_chain": "补贴门槛抬高至 300Wh/kg → 中小电池厂无法达标 → 行业集中度 CR4 从 73% → 82% → 公司份额结构性上升",
        "estimated_impact": "2027 年市占率从 38% → 44%，对应额外 EPS +0.54 元"
      }
    ],
    "conclusion": "政策明显利好本股。新补贴标准实质上是壁垒强化工具，公司高端技术储备(Kirin 4.0) 转化为市场份额增益"
  }
}
```

注意：
- 每条 evidence 都有**具体 URL**
- association 标明**挂钩到哪个其他维度**
- conclusion 明确表态（利好 / 利空 / 中性），不和稀泥
- 给出**可验证的量化估算**（市占率变动、EPS 影响）
