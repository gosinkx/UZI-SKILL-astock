# Data Contracts · JSON Schema 契约

5 个 Task 之间通过 JSON 文件传递数据。**修改字段名前必须同步更新本文件和 report-template.html。**

## 1. raw_data.json (Task 1 产物)

```json
{
  "ticker": "002273.SZ",
  "name": "水晶光电",
  "market": "A",
  "fetched_at": "2026-04-14T12:34:56+08:00",
  "dimensions": {
    "0_basic": {
      "data": {
        "code": "002273.SZ",
        "name": "水晶光电",
        "industry": "光学光电",
        "market_cap": 25860000000,
        "price": 18.56,
        "change_pct": 2.32,
        "pe_ttm": 42.3,
        "pb": 4.12,
        "one_liner": "国内精密光学薄膜龙头"
      },
      "source": "akshare:stock_individual_info_em",
      "fallback": false
    },
    "1_financials": { "data": {...}, "source": "...", "fallback": false },
    "...": "...",
    "20_valuation_models": {
      "data": {
        "dcf": {
          "wacc_breakdown": {"wacc": 0.0696, "cost_of_equity": 0.085, "after_tax_kd": 0.034},
          "base_fcf_yi": 8.24,
          "projected_fcf_yi": [9.06, 9.97, 10.97, ...],
          "pv_explicit_yi": 89.7,
          "terminal_value_yi": 450.0,
          "tv_pv_yi": 198.6,
          "tv_pct_of_ev": 69.0,
          "enterprise_value_yi": 288.3,
          "equity_value_yi": 288.3,
          "intrinsic_per_share": 20.73,
          "current_price": 29.03,
          "safety_margin_pct": -28.6,
          "verdict": "🟠 略微高估",
          "sensitivity_table": {"wacc_axis": [...], "g_axis": [...], "values_per_share": [[...], ...], "center_cell": 20.73},
          "methodology_log": ["Step 1 · WACC: ...", "Step 2 · 基期 FCF=...", "..."]
        },
        "comps": {
          "peer_stats": {"pe": {...}, "pb": {...}, ...},
          "target_percentile": {"pe": 0, "pb": 30, ...},
          "implied_price": {"via_median_pe": 59.98},
          "valuation_verdict": "🟢 便宜（PE 低于 75% 同行）"
        },
        "three_statement": {
          "years": ["Y1", "Y2", "Y3", "Y4", "Y5"],
          "income_statement": {"revenue": [...], "net_income": [...]},
          "cash_flow": {"fcf": [...]}
        },
        "lbo": {
          "entry_ebitda_yi": 17.17,
          "irr_pct": 21.7,
          "moic": 2.67,
          "verdict": "🟢 PE 买方可赚 20%+ IRR"
        },
        "summary": {
          "dcf_intrinsic": 20.73,
          "dcf_safety_margin_pct": -28.6,
          "lbo_irr_pct": 21.7,
          "comps_verdict": "🟢 便宜..."
        }
      },
      "source": "compute:fin_models (DCF/Comps/3-stmt/LBO)",
      "fallback": false
    },
    "21_research_workflow": {
      "data": {
        "initiating_coverage": {
          "headline": {"rating": "减持 (Underperform)", "target_price": 20.73, "current_price": 29.03, "upside_pct": -28.6},
          "executive_summary": "...",
          "investment_thesis": [{"pillar": "...", "evidence": "...", "weight": "High"}],
          "key_risks": [{"risk": "...", "severity": "High", "detail": "..."}]
        },
        "earnings_analysis": {"headline": "双超预期...", "beat_miss": {...}},
        "catalyst_calendar": {
          "events": [{"date": "2026-04-15", "event": "...", "category": "past|forward|risk", "impact": "high|medium|low"}],
          "high_impact_count": 1,
          "past_event_count": 10,
          "forward_event_count": 4
        },
        "thesis_tracker": {"pillars_passed": 3, "pillars_total": 5, "thesis_intact_pct": 60, "conviction": "Medium"},
        "morning_note": {"top_call": "...", "bullets": ["..."]},
        "idea_screens": {"value": {...}, "growth": {...}, "quality": {...}, "gulp": {...}, "short": {...}},
        "sector_overview": {"industry": "...", "market_size": {...}},
        "summary": {...}
      }
    },
    "22_deep_methods": {
      "data": {
        "ic_memo": {
          "sections": {
            "I_exec_summary": {"headline": "⚪ 观望 (HOLD)", "recommendation": "...", "top_3_risks": [...]},
            "VII_returns_scenarios": [
              {"scenario": "Bull", "price_target": 26.95, "return_pct": -7.2, "probability_pct": 25},
              {"scenario": "Base", "price_target": 20.73, "return_pct": -28.6, "probability_pct": 50},
              {"scenario": "Bear", "price_target": 14.51, "return_pct": -50.0, "probability_pct": 25}
            ]
          }
        },
        "competitive_analysis": {
          "porter_five_forces": {
            "new_entrants_threat": {"score": 3, "rationale": "..."},
            "substitutes_threat": {"score": 3, "rationale": "..."},
            "supplier_power": {"score": 3, "rationale": "..."},
            "buyer_power": {"score": 3, "rationale": "..."},
            "rivalry_intensity": {"score": 3, "rationale": "..."}
          },
          "bcg_position": {"category": "Dog (瘦狗)", "strategic_action": "..."},
          "industry_attractiveness_pct": 50
        },
        "unit_economics": {"business_type": "non-recurring", "waterfall": [...]},
        "value_creation_plan": {"levers": [...], "total_uplift_yi": 6.75},
        "dd_checklist": {"workstreams": [...], "completion_pct": 48, "manual_review_required": 11},
        "portfolio_rebalance": {...}
      }
    }
  }
}
```

## 2. dimensions.json (Task 2 产物)

```json
{
  "ticker": "002273.SZ",
  "fundamental_score": 78.4,
  "dimensions": {
    "1_financials": {
      "score": 8,
      "weight": 5,
      "label": "财报扎实",
      "reasons_pass": ["ROE 连续 3 年 > 18%", "净利率 22%"],
      "reasons_fail": ["商誉占净资产 35%"],
      "raw_pointer": "raw_data.json#/dimensions/1_financials"
    }
  }
}
```

## 3. panel.json (Task 3 产物)

```json
{
  "ticker": "002273.SZ",
  "panel_consensus": 64.2,
  "vote_distribution": {
    "strongly_buy": 8, "buy": 12, "watch": 18, "wait": 7, "avoid": 3, "n_a": 2
  },
  "signal_distribution": {
    "bullish": 24, "neutral": 17, "bearish": 9
  },
  "investors": [
    {
      "investor_id": "buffett",
      "name": "巴菲特",
      "group": "A",
      "avatar": "avatars/buffett.svg",
      "signal": "bullish",
      "confidence": 87,
      "score": 82,
      "verdict": "买入",
      "reasoning": "...",
      "comment": "...",
      "pass": ["..."],
      "fail": ["..."],
      "ideal_price": 16.20,
      "period": "3-5 年"
    }
  ]
}
```

## 4. synthesis.json (Task 4 产物 · v2.0)

完整结构见 `references/task4-synthesis.md` 末尾。关键字段：

### 脚本生成（stub）
- `overall_score`: 0-100
- `verdict_label`: 五档定调
- `fundamental_score`, `panel_consensus`
- `institutional_modeling`: dim 20/21/22 的汇总引用（DCF intrinsic / LBO IRR / IC recommendation / BCG 等）

### Claude 必须重写
- `debate`: bull/bear/rounds[]/judge_verdict/punchline **— 每段必须引用具体数字**
- `great_divide.punchline`: 20-30 字冲突金句
- `dashboard.core_conclusion`: 1-2 句有定论的结论
- `buy_zones.*.rationale`: 每个价位必须有计算逻辑
- `risks[]`: 具体到数字 / 事件
- `dim_commentary`: 每个维度 1-2 句定性评语（回答 5 个问题：数据可信吗 / 背后故事 / 同行对比 / 结构性问题 / 对论点影响）
- `institutional_triangulation.conflict_note`: 解释 DCF/Comps/LBO 为何一致或冲突
- `adjusted_dcf` (可选): 如果默认假设不合理，重跑后的 DCF 结果

### 完整 v2.0 schema 示例

```json
{
  "ticker": "002273.SZ",
  "name": "水晶光电",
  "overall_score": 60.1,
  "verdict_label": "观望优先",
  "fundamental_score": 66.1,
  "panel_consensus": 50.9,
  "dim_commentary": {
    "1_financials": "[Claude 写] ROE 从 2021 年 18% 掉到 2024 年 11.8%...",
    "2_kline": "[Claude 写] Stage 2 但距 60 日高点仅 -5%...",
    "14_moat": "[Claude 写] 无形资产 + 规模优势合计 27/40..."
  },
  "institutional_modeling": {
    "dcf_intrinsic": 20.73,
    "dcf_safety_margin_pct": -28.6,
    "dcf_verdict": "🟠 略微高估",
    "lbo_irr_pct": 21.7,
    "lbo_verdict": "🟢 PE 买方可赚 20%+ IRR",
    "initiating_rating": "减持 (Underperform)",
    "target_price": 20.73,
    "upside_pct": -28.6,
    "ic_recommendation": "⚪ 观望 (HOLD)",
    "bcg_position": "Dog (瘦狗)"
  },
  "institutional_triangulation": {
    "conflict_note": "[Claude 写] DCF 说高估 28% 但 LBO 说 PE 仍赚 21% IRR — 市场对光学行业增速假设偏悲观"
  },
  "debate": {
    "bull": {"investor_id": "livermore", "name": "利弗莫尔"},
    "bear": {"investor_id": "klarman", "name": "卡拉曼"},
    "rounds": [
      {"round": 1, "bull_say": "Stage 2 + 60 日均线站稳...", "bear_say": "DCF 安全边际 -28%，技术面是空中楼阁..."}
    ],
    "punchline": "[Claude 写] DCF 说高估 28%，但 PE 买方仍能赚 21% IRR —  分歧本身才是信息。"
  },
  "great_divide": {
    "bull_avatar": "livermore", "bear_avatar": "klarman",
    "bull_score": 100, "bear_score": 0,
    "punchline": "[同 debate.punchline]"
  },
  "buy_zones": {
    "value":     {"price": 17.62, "rationale": "DCF 内在价 ¥20.73 × 0.85 安全边际"},
    "growth":    {"price": 18.05, "rationale": "Y3 EPS 预测 × 同行中位 PE"},
    "technical": {"price": 27.50, "rationale": "60 日均线支撑位"},
    "youzi":     {"price": 29.03, "rationale": "龙虎榜未出现集中卖出"}
  },
  "risks": [
    "ROE 5 年最低 6.7%，达标率 0/5 (巴菲特规则)",
    "PE 35x 高于格雷厄姆 15x 标准",
    "DCF 安全边际 -28%"
  ],
  "dashboard": {
    "core_conclusion": "[Claude 写] 水晶光电 · 60 分 · 观望优先。机构建模说减持，但 LBO 视角 IRR 21% — 分歧来自行业增速假设。",
    "intelligence": {
      "news": "...",
      "risks": [...],
      "catalysts": [...]
    },
    "battle_plan": {...}
  }
}
```

## 5. 输出文件

```
reports/{ticker}_{YYYYMMDD}/
├── full-report.html        # 主报告
├── share-card.png          # 1080×1920 朋友圈
├── war-report.png          # 1920×1080 微信群
├── one-liner.txt           # 一句话
└── kline.png               # K 线快照（assemble_report.py 顺手出）
```

## 缓存目录

```
.cache/{ticker}/
├── raw_data.json          # Task 1
├── dimensions.json        # Task 2
├── panel.json             # Task 3
├── synthesis.json         # Task 4
└── api_cache/             # data_sources.py 的 24h 接口缓存
    ├── stock_zh_a_hist__002273__daily.json
    ├── stock_individual_info_em__002273.json
    └── ...
```
