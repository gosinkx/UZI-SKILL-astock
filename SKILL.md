---
name: uzi-stock-astock
description: 优化版 UZI-Skill — A股/港股/美股个股深度分析引擎。V3.10 核心优化：A 股数据源重排为腾讯直连(主) + akshare(次) + 东财限流(兜底)
version: 3.10.0
author: gosinkx (基于 wbh604/UZI-Skill v3.9.1)
license: MIT
---

# UZI-SKILL-astock · UZI-Skill 优化版

基于 [UZI-Skill v3.9.1](https://github.com/wbh604/UZI-Skill) 的 A 股数据源架构优化版本。

## V3.10 优化内容

| 优化项 | 级别 | 说明 |
|--------|------|------|
| 腾讯 qt 提升为主数据源 | P0 | 行情/PE/PB/市值优先走腾讯 qt.gtimg.cn（不封IP），替代 akshare XueQiu 4次重试 |
| 东财统一限流 em_get() | P0 | 所有直连东财 HTTP 请求走串行限流（≥1s+随机抖动），对标 a-stock-data 防封策略 |
| K 线 fallback 链重排 | P1 | 非东财源优先：新浪直连→腾讯直连→baostock→akshare→东财(限流) |
| 新浪财报三表 fallback | P1 | akshare 财报失败时自动降级到新浪 quotes.sina.cn 直连 |

## 子技能

- `deep-analysis` — 核心深度分析工作流（22维×65评委×17方法）
- `investor-panel` — 65位大佬投资者评审团
- `lhb-analyzer` — 龙虎榜分析
- `trap-detector` — 杀猪盘检测

## 快速开始

```bash
pip install akshare yfinance baostock pandas requests mplfinance rich playwright ddgs
python run.py 贵州茅台
```

## 数据源优先级（V3.10）

| 优先级 | 数据源 | 封IP风险 | 用途 |
|--------|--------|---------|------|
| 1 | 腾讯 qt.gtimg.cn | 不封 | 实时价/PE/PB/市值 |
| 2 | 新浪 money.finance.sina.cn | 不封 | K线、财报三表 |
| 3 | baostock | 不封 | K线兜底 |
| 4 | akshare (XueQiu/新浪) | 极低 | Enriched F10/公司资料 |
| 5 | 东财 push2/push2his | 有风控(限流) | 仅用于独有数据 |

## 原项目

- 上游: https://github.com/wbh604/UZI-Skill
- 优化来源: [a-stock-data](https://github.com/simonlin1212/a-stock-data) 架构思路
