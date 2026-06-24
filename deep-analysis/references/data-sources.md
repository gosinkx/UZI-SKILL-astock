# 📡 DATA_SOURCES · 每个字段的稳定来源清单

> **核心规则**：报告里看到的每一块数据，都必须在本文件里找到对应的**稳定来源 + 三级 fallback**。
> 如果某字段找不到稳定源，它就不应该出现在报告里——禁止让 Claude 瞎编。
>
> **优先级规则（V3.10 重排）**：遵循「不封IP的源优先」原则
> - **A**: 腾讯 qt.gtimg.cn / 新浪直连 HTTP（不封IP，零鉴权，最优先）
> - **B**: akshare 主接口（次级，依赖第三方库）
> - **C**: 东财直连 HTTP（仅用于独有数据，走 `em_get()` 限流）
> - **D**: baostock / Web search + Claude（兜底）
> - **E**: 标记"数据缺失"，卡片不渲染该字段
>
> 所有数据调用都必须走 `lib/data_sources.py`，里面已经有 24h 分级缓存 + retry + 东财限流。

---

## 0 · 股票基础信息

| 字段 | A 主源（V3.10，不封IP） | B 备源 | C 兜底 |
|---|---|---|---|
| `name` 股票简称 | **腾讯 qt.gtimg.cn** → `name(field 1)` | `akshare.stock_individual_info_em` → `股票简称` | baostock |
| `industry` 行业 | `akshare` XueQiu F10 → `affiliate_industry` | `stock_board_industry_cons_em` 反查 | `_known_stock_industry` 内置映射 |
| `market_cap` 市值 | **腾讯 qt.gtimg.cn** → `总市值(field 45)` | akshare `stock_individual_info_em` | 东财 push2 JSON（em_get限流）|
| `price` 最新价 | **腾讯 qt.gtimg.cn** → `最新价(field 3)` (TTL 60s) | akshare XueQiu spot_xq | 东财 push2 / baostock |
| `change_pct` 涨跌幅 | **腾讯 qt.gtimg.cn** → 自算 (price-prev)/prev | akshare XueQiu spot_xq → `涨幅` | 东财 push2 |
| `pe_ttm` | **腾讯 qt.gtimg.cn** → `PE(TTM)(field 39)` | akshare XueQiu spot_xq → `市盈率(TTM)` | baidu gushitong / baostock |
| `pb` | **腾讯 qt.gtimg.cn** → `PB(field 46)` | akshare XueQiu spot_xq → `市净率` | baidu gushitong / baostock |
| `one_liner` 一句话定位 | web search "{name} 主营业务" | Claude 从 `stock_zygc_em` 生成 | Claude 从行业+市值 生成 |

**港股**: 用 `stock_hk_spot_em` / `stock_hk_hist`
**美股**: 用 `yfinance.Ticker(code).info`

---

## 1 · 财报 (Dim 1)

viz 需要的字段 → 来源：

| viz 字段 | A 主源 | 备注 |
|---|---|---|
| `roe_history` 5年ROE | `stock_financial_analysis_indicator(symbol)` → `加权净资产收益率(%)` | 取最近 5 年年末值 |
| `revenue_history` 5年营收 | `stock_financial_abstract(symbol)` → `营业总收入` | 单位换算到亿 |
| `net_profit_history` 5年净利 | `stock_financial_abstract` → `归属母公司所有者的净利润` | 同上 |
| `financial_years` 年度标签 | `stock_financial_abstract` → `报告期` | 格式化 "2020"/"25Q1" |
| `dividend_years` 分红年度 | `stock_history_dividend_detail(symbol)` → `公告日期` | |
| `dividend_amounts` 分红金额 | `stock_history_dividend_detail` → `派息` (元/10股) | |
| `dividend_yields` 股息率 | 自算: `dividend / price_at_year_end * 100` | 基于 kline 收盘价 |
| `financial_health.current_ratio` | `stock_financial_analysis_indicator` → `流动比率` | |
| `financial_health.debt_ratio` | `stock_financial_analysis_indicator` → `资产负债率(%)` | |
| `financial_health.fcf_margin` | 自算: `经营现金流 / 净利润 * 100` from `stock_cash_flow_sheet_by_report_em` | |
| `financial_health.roic` | `stock_financial_analysis_indicator` → `总资产净利率(%)` | 近似 |

**港股 fallback**: `stock_hk_financial_abstract`
**美股 fallback**: `yfinance.Ticker.financials` + `.balance_sheet` + `.cashflow`

---

## 2 · K 线 (Dim 2)

| viz 字段 | A 主源 (akshare) | B 直连 HTTP | C |
|---|---|---|---|
| `candles_60d` OHLC 60日 | `stock_zh_a_hist(symbol, period='daily', adjust='qfq')` 取最后 60 行 | 东财 `push2his.eastmoney.com/api/qt/stock/kline/get` secid=1/0.{code} klt=101 fqt=1 | 新浪 `quotes_service/api/json_v2.php/CN_MarketData.getKLineData` |
| `ma20_60d` MA20 序列 | 自算: rolling mean of 20 日收盘 | 同上 | 同上 |
| `ma60_60d` MA60 序列 | 自算: rolling mean of 60 日收盘 | 同上 | 同上 |
| `close_60d` 60日收盘 | `stock_zh_a_hist` 的 `收盘` 列 | 同上 | 同上 |
| `stage` Weinstein 阶段 | 自算: 基于价格 vs MA200 + MA200 斜率 | — | — |
| `ma_align` 均线排列 | 自算: MA5>MA10>MA20>MA60 判断 | — | — |
| `macd` | 自算 (ema12, ema26, dif, dea) | — | — |
| `rsi` | 自算 RSI14 | — | — |
| `kline_stats.beta` | `akshare.stock_zh_index_hist_em('sh000001')` 相关性 计算 | web | — |
| `kline_stats.volatility` | 自算: std(daily_return) * sqrt(252) | — | — |
| `kline_stats.max_drawdown` | 自算: `(trough - peak) / peak` 近 1 年 | — | — |
| `kline_stats.ytd_return` | 自算: `(last - ytd_open) / ytd_open` | — | — |

**7 路 fallback 链（V3.10 重排，不封IP优先）** 已在 `lib/data_sources.py::_kline_a_share_chain` 实现：
1. 新浪直连 `money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData`（不封IP）
2. 腾讯直连 `web.ifzq.gtimg.cn/appstock/app/fqkline/get`（不封IP）
3. baostock `query_history_k_data_plus`（官方接口）
4. akshare `stock_zh_a_daily`（新浪）
5. akshare `stock_zh_a_hist`（东财）
6. 东财直连 push2his（`em_get` 限流）
7. providers chain（tushare / efinance 兜底）

---

## 3 · 宏观 (Dim 3) · qualitative

Claude web search only，不走 akshare。prompt 模板在 `fetch_macro.py`。

---

## 4 · 同行对比 (Dim 4)

| viz 字段 | A 主源 | B 备源 |
|---|---|---|
| `peer_table` 行业前 5 同类 | `stock_board_industry_cons_em(industry_name)` 取 top 5 by 市值 | `stock_sector_spot('sw')` 按行业分组 |
| `peer_comparison` 自己 vs 均值 | peer_table 聚合算均值 | — |

每条 peer 需要 `pe / pb / roe / revenue_growth` → 对每个 peer 再查一次 `stock_individual_info_em` + `stock_financial_analysis_indicator`。

---

## 5 · 上下游 (Dim 5)

| viz 字段 | A 主源 | B 备源 |
|---|---|---|
| `main_business_breakdown` 主营饼 | `stock_zygc_em(symbol)` → `分产品/分地区` | 同花顺 F10 scrape |
| `upstream` 上游描述 | Claude 从 `stock_zygc_em` + web search 生成 | — |
| `downstream` 下游描述 | web search "{name} 下游客户 前五大" | — |
| `client_concentration` 客户集中度 | cninfo 年报附注 scrape "前五大客户" | web search |
| `supplier_concentration` 供应商集中度 | cninfo 年报附注 scrape "前五大供应商" | web search |

---

## 6 · 研报 (Dim 6)

| viz 字段 | A 主源 |
|---|---|
| `coverage` 覆盖券商数 | `stock_research_report_em(symbol)` count unique orgs |
| `rating` 评级分布 | 同上，聚合 `评级` 字段 |
| `target_avg` / `target_max` / `target_min` | 同上，聚合 `目标价` 字段 |
| `recent_reports` 近 10 研报 | 同上 head(10) |

---

## 7 · 行业景气 (Dim 7)

| viz 字段 | A 主源 |
|---|---|
| `growth` 行业增速 | web search "{industry} 2026 行业增速" |
| `tam` 市场规模 | web search "{industry} TAM 市场规模" |
| `penetration` 渗透率 | web search |
| `lifecycle` 生命周期 | Claude 判断（导入/成长/成熟/衰退）|
| `matched_boards` 概念板块关联 | `stock_board_concept_name_em()` filter by name contains | 

---

## 8 · 原材料 (Dim 8)

| viz 字段 | A 主源 | B 备源 |
|---|---|---|
| `core_material` 核心材料 | web search "{name} 原材料 采购" + 年报解析 | — |
| `price_history_12m` 价格走势 | `futures_spot_price_daily` (for 大宗) / 生意社 `sci99.com` scrape | web search |
| `cost_share` 成本占比 | 年报附注 | web search |
| `import_dep` 进口依赖 | web search | — |

---

## 9 · 期货关联 (Dim 9) · qualitative only

Web search identify linked contract → `futures_main_sina` for price.

---

## 10 · 估值 (Dim 10)

| viz 字段 | A 主源 |
|---|---|
| `pe` 当前 PE | `stock_a_indicator_lg(symbol)` 最后一行 `pe` |
| `pe_history` 5 年 PE | `stock_a_indicator_lg` 最后 1250 行 `pe` 列 |
| `pe_quantile` 5 年分位 | 自算 rank percentile |
| `pb` 当前 PB | `stock_a_indicator_lg` → `pb` |
| `pb_quantile` | 自算 |
| `industry_pe` 行业均值 | `stock_board_industry_cons_em(industry)` 的 `市盈率-动态` 均值 |
| `dcf.intrinsic_value` | 自算: `simple_dcf(fcf, growth, wacc)` in fetch_valuation |
| `dcf_sensitivity.values` | 自算: 5×4 矩阵 (WACC × growth) |
| `dcf_sensitivity.waccs` | [8, 9, 10, 11, 12] 固定 |
| `dcf_sensitivity.growths` | [6, 8, 10, 12] 固定 |

---

## 11 · 治理 (Dim 11)

| viz 字段 | A 主源 |
|---|---|
| `pledge` 实控人质押 | `stock_gpzy_pledge_ratio_em()` filter |
| `insider` 近 12 月增减持 | `stock_ggcg_em(symbol='近一年')` aggregate |
| `related_tx` 关联交易占比 | cninfo 年报附注 scrape |
| `violations` 违规记录 | `stock_zh_a_st_em()` check |
| `equity_incentive` 股权激励 | `akshare.stock_gpzy_profile_em` 或 cninfo |
| `executive_list` 管理层 | cninfo `stock_zh_a_executive_em` |
| `exec_compensation` 薪酬 | 年报 |

---

## 12 · 资金面 (Dim 12)

| viz 字段 | A 主源 |
|---|---|
| `northbound_history` 北向 20 日 | `stock_hsgt_individual_em(stock=code)` tail 20 |
| `northbound_20d` 净买入汇总 | 上行 sum |
| `margin_history` 融资余额 | `stock_margin_detail_szse(date)` / `stock_margin_detail_sse(date)` filter by code |
| `margin_trend` 趋势描述 | 自算 |
| `holders_history` 股东户数 | `stock_zh_a_gdhs(symbol=code)` head 8 |
| `holders_trend` | 自算 连升/连降 |
| `main_history` 主力 5 日 | `stock_individual_fund_flow(stock, market)` tail 5 |
| `main_5d` 汇总 | 上行 sum |
| `block_trades_recent` 大宗交易 | `stock_dzjy_mrtj(start_date, end_date)` filter |
| `unlock_schedule` 12 月解禁 | `stock_restricted_release_queue_sina(symbol)` / `stock_restricted_release_detail_em(start, end)` filter | 
| `institutional_history.quarters` 季度 | `stock_report_fund_hold_detail(symbol, date)` 近 8 季聚合 |
| `institutional_history.fund` 公募持仓 | 同上，type 过滤"公募" |
| `institutional_history.qfii` QFII 持仓 | 同上，type 过滤"QFII" |
| `institutional_history.shehui` 社保持仓 | 同上，type 过滤"社保" / 年金 |

---

## 13 · 政策 (Dim 13) · qualitative only

Web search + Claude 判断。

---

## 14 · 护城河 (Dim 14)

| viz 字段 | A 主源 |
|---|---|
| `rd_investment` 研发投入 | `stock_financial_analysis_indicator` → `营业总成本(元)` - 年报研发费用 |
| `rd_pct` 研发占比 | 自算 |
| `patent_count` 专利数 | web search "{name} 专利数量" / 国家知识产权局 scrape |
| `intangible` / `switching` / `network` / `scale` | Claude 从业务描述 + 同行对比 评估 (1-10) |

---

## 15 · 事件驱动 (Dim 15)

| viz 字段 | A 主源 |
|---|---|
| `event_timeline` 事件时间线 | `stock_news_em(symbol)` + `stock_notice_report` + `stock_telegraph_cls` 合并按日期排序 |
| `recent_news` 近新闻 | `stock_news_em(symbol)` head 10 |
| `catalyst` 催化剂 | Claude 从 timeline 提炼 |
| `earnings_preview` 业绩预告 | `stock_yjbb_em(date)` filter by code |
| `warnings` 利空 | `stock_zh_a_st_em` + web search |

---

## 16 · 龙虎榜 (Dim 16)

| viz 字段 | A 主源 |
|---|---|
| `lhb_records` 30 日上榜 | `stock_lhb_stock_detail_em(symbol, date)` |
| `matched_youzi` 识别游资 | `lib/seat_db::match_seats_in_lhb()` |
| `inst_vs_youzi.inst_net` 机构净买 | 自算，识别"机构专用"席位 |
| `inst_vs_youzi.youzi_net` 游资净买 | 自算 |
| `sector_lhb` 同板块 | `stock_lhb_stock_statistic_em(symbol='近一月')` |

---

## 17 · 舆情 (Dim 17)

| viz 字段 | A 主源 |
|---|---|
| `xueqiu_heat` 雪球热度 | `stock_hot_rank_detail_em(symbol)` head 30 |
| `guba_volume` 股吧讨论量 | 爬 `guba.eastmoney.com/list,{code}.html` 帖子数 |
| `big_v_mentions` 大 V 提及 | web search "雪球 {name}" 聚合 |
| `positive_pct` 正面占比 | web search + Claude 情感分析 |
| `thermometer_value` 温度计 | 自算 0-100 归一化 |

---

## 18 · 杀猪盘检测 (Dim 18) · qualitative

8 信号扫描全部靠 Claude web search，详见 `skills/trap-detector/references/eight-signals.md`。

---

## 19 · 实盘比赛持仓 (Dim 19)

| viz 字段 | A 主源 |
|---|---|
| `xq_cubes_list` 雪球组合列表 | `https://xueqiu.com/cubes/cubes_search.json?code={symbol}` + cookie (已在 fetch_contests 实现) |
| `high_return_cubes` 高收益数 | 过滤 total_gain > 50 |
| `tgb_list` 淘股吧讨论 | `https://www.taoguba.com.cn/Article/list/all?keyword={code}` HTML scrape |
| `ths_list` 同花顺模拟 | `https://moni.10jqka.com.cn/holder/?stock={code}` scrape |

---

## 🌟 NEW · 基金经理抄作业 (Fund Managers)

**这是新增的面板，最需要稳定源**。

| viz 字段 | A 主源 |
|---|---|
| `fund_holders` 持仓基金列表 | `stock_report_fund_hold_detail(symbol, date)` 最近 1-2 季所有持仓基金 |
| `fund_code` 基金代码 | 同上返回 |
| `fund_name` 基金名称 | 同上 |
| `position_pct` 占基金比例 | 同上 `占净值比例` |
| `rank_in_fund` 第几大持仓 | 同上 `排名` |
| `holding_quarters` 持有季度数 | 查近 8 季历史 `stock_report_fund_hold_detail` 判断 |
| `position_trend` 加仓/减仓 | 对比上季 `持股数量` 变化 |
| `manager_name` 基金经理 | `fund_em_manager_thsi(fund_code)` 或 `fund_manager_em()` match |
| `nav_history` 5 年净值 | `fund_open_fund_info_em(symbol=fund_code, indicator='累计净值走势')` tail 5Y |
| `return_5y` 5 年累计收益 | 自算: `(nav[-1] - nav[0]) / nav[0] * 100` |
| `annualized_5y` 年化 | 自算: `((1+return_5y/100)^(1/5) - 1) * 100` |
| `max_drawdown` 最大回撤 | 自算: peak-trough on nav |
| `sharpe` 夏普比率 | 自算: mean(daily_ret) / std(daily_ret) * sqrt(252) · 无风险利率按 3% |
| `peer_rank_pct` 同类排名 | `fund_manager_em()` + `fund_em_rank_detail` |
| `fund_url` 基金详情链接 | `https://fund.eastmoney.com/{fund_code}.html` |

**Fallback**:
- B: `fund_em_daily_info` + `fund_em_rating` 组合
- C: web search "{基金名称} 5年业绩" + 天天基金网 scrape

---

## 🌟 NEW · 相似股推荐 (Similar Stocks)

| viz 字段 | A 主源 | B 备源 |
|---|---|---|
| `similar_stocks` 前 4 只 | 方法: 同行业 + 概念板块交集 + 股价相关性 > 0.8 | — |
| 数据路径 | `stock_board_industry_cons_em(industry)` ∩ `stock_board_concept_cons_em(concept)` 然后对每个候选算 60 日收益率 pearson 相关 | `stock_zh_a_spot_em` 全表相似度 |
| `similarity` 相似度 % | 自算: 相关系数 * 100 |
| `reason` 理由 | Claude 从业务描述 生成 1 句 |

---

## 🌟 NEW · 情景模拟 (Scenario Simulator)

| 场景 | 计算方法 |
|---|---|
| `最坏情况 (-35%)` | entry_price × (1 - 2σ) — 2 倍历史年化波动率 |
| `偏差情况 (-15%)` | entry_price × (1 - 1σ) |
| `合理情况 (+12%)` | entry_price × (1 + 预期收益率)，基于研报目标价均值 |
| `乐观情况 (+38%)` | entry_price × (1 + 1σ + 预期收益率) |
| `极致乐观 (+75%)` | entry_price × (1 + 2σ + 预期收益率) |

`probability` 基于正态分布假设（实际是经验值）:
- -2σ: 5%
- -1σ: 25%
- base: 40%
- +1σ: 25%
- +2σ: 5%

---

## 🌟 NEW · 离场触发条件 (Exit Triggers)

Claude **从 synthesis 自动生成 5 条**，模板：

1. **技术止损**: "股价跌破 {MA60 值} (60 日均线) → 无条件止损"
2. **基本面恶化**: "{关键依赖} 下修 > 10% → 业绩逻辑动摇" (从 raw_data.5_chain 提取大客户)
3. **业绩不达**: "下次业绩预告低于 +{当前增速下限}% → 预期管理失守"
4. **资金撤离**: "{识别到的顶级游资} 席位大额卖出 > 2 亿 → 顶级游资撤离信号"
5. **估值泡沫**: "PE 站上 5 年 {current + 15}% 分位 → 泡沫区获利了结"

---

## ⚙️ 缓存 TTL 规则（来自 `lib/cache.py`）

| 数据类型 | TTL | 举例 |
|---|---|---|
| `TTL_REALTIME` = 60s | 实时行情 | 价格、涨跌幅、市值 |
| `TTL_INTRADAY` = 5min | 盘中数据 | K 线、筹码分布、主力资金、雪球热度 |
| `TTL_HOURLY` = 1h | 小时级 | 个股新闻 |
| `TTL_DAILY` = 2h | 日度聚合 | 龙虎榜、北向、融资融券 (覆盖收盘后窗口) |
| `TTL_QUARTERLY` = 24h | 低频 | 财报、研报、历史估值、机构持仓、分红 |
| `TTL_STATIC` = 7d | 几乎不变 | 行业分类、股票简称 |

**强刷**: `STOCK_NO_CACHE=1` 环境变量绕过全部缓存。

## 🔒 东财限流策略（V3.10 新增）

所有直连东财的 HTTP 请求统一走 `em_get()` 函数，自动做到：
- **串行**：全局锁，绝不对东财开并发
- **≥1s 间隔 + 随机抖动** (±0.3s)
- **会话复用**：同 Keep-Alive 连接
- **默认 UA + Referer**

> 对标 `a-stock-data` V3.2 防封策略。东财仅用于其独有数据（龙虎榜/解禁/两融等），行情/K线已优先使用腾讯/新浪直连。

---

## 🛡️ 数据质量约定

1. **每条数据必须带 `source` 字段**：告诉前端这条数据是哪个接口拉的
2. **`fallback=True` 标记**：用 web search 兜底时必须标记，报告前端显示 "[网络搜索]" 徽章而非 "[官方接口]"
3. **缺失不编造**：找不到数据时字段置 `null` 或缺席，viz 自动跳过渲染该 sub-panel
4. **akshare 版本锁定**：requirements.txt 锁 `akshare>=1.14.0` (API 在此版本后稳定)
5. **接口失败重试 3 次后才走 fallback 链**：见 `lib/data_sources.py::_retry`

---

## 🔍 已知问题 / TODO

- [ ] `stock_report_fund_hold_detail` 返回格式不稳定，不同季度字段名可能变化，需要多版本适配
- [ ] `cninfo` 年报附注（客户/供应商集中度）没有结构化 API，只能 PDF 解析 → 暂时依赖 web search
- [ ] 港股/美股的基金持仓数据源比 A 股弱，fund_managers 面板对港美股初期可能为空
- [ ] 雪球 cookie 6 小时过期，`lib/data_sources.py::_xq_session` 目前没有刷新机制
- [ ] 淘股吧对爬虫有 WAF，高频访问会被封，建议单次查询 + 缓存 24h

---

**维护者**: 任何 fetcher 的字段变动必须同步更新本文件。本文件是 single source of truth。
