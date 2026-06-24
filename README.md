# UZI-SKILL-astock

> UZI-Skill v3.9.1 → **V3.10 数据源架构优化版**

基于 [UZI-Skill](https://github.com/wbh604/UZI-Skill) 的 A 股数据源专项优化，借鉴 [a-stock-data](https://github.com/simonlin1212/a-stock-data) 的架构思路，核心解决 akshare 东财接口被封 IP、重试等待时间长的问题。

## V3.10 变更日志

### P0：行情层替换为腾讯 qt.gtimg.cn 主路径

**改动**：`lib/data_sources.py` 中 `_fetch_basic_a()` 的 fallback 链重排

```
旧路径: MX(可选) → XueQiu ×4次重试(8s) → push2 → Tencent(兜底)
新路径: MX(可选) → Tencent(1次, 不封IP) → XueQiu ×2次(补充F10)
```

- 腾讯 qt 接口实测返回茅台 **1216.06元 / PE=18.38 / PB=5.67**
- XueQiu 重试次数从 4 次降为 2 次（腾讯已有价格时跳过）
- 行情获取总等待时间：旧方案最快 8s → 新方案最快 1s

### P0：东财统一限流层 em_get()

**新增** `lib/data_sources.py` 中的 `em_get()` 函数，所有直连东财 HTTP 调用统一走此入口：

- 全局串行锁（绝不对东财开并发）
- ≥1s 间隔 + 随机抖动 ±0.3s
- 会话复用（Keep-Alive）
- 默认 UA + Referer

> 对标 a-stock-data V3.2 防封策略

### P1：K 线 fallback 链重排

```
旧: akshare东财(1) → akshare新浪(2) → baostock(3) → 东财直连(4) → 新浪直连(5) → 腾讯直连(6)
新: 新浪直连(1) → 腾讯直连(2) → baostock(3) → akshare新浪(4) → akshare东财(5) → 东财直连[限流](6)
```

前两个源（新浪、腾讯）实测不封 IP，覆盖 ~90% K 线需求。

### P1：新浪财报三表 fallback

`_fetch_financials_impl()` 在 akshare 财报接口失败时，自动降级到新浪 `quotes.sina.cn` 直连（不封 IP），覆盖利润表/资产负债表/现金流量表。

## 安装

```bash
pip install akshare yfinance baostock pandas requests mplfinance rich playwright ddgs
playwright install chromium  # 可选，用于截图

python run.py 贵州茅台
python run.py AAPL
python run.py 00700.HK
```

## 与原版差异

| 对比项 | UZI-Skill v3.9.1 | UZI-SKILL-astock v3.10 |
|--------|-------------------|------------------------|
| 行情主源 | akshare XueQiu（4次重试） | 腾讯 qt.gtimg.cn（1次） |
| 东财调用限流 | 无 | em_get() 串行限流 ≥1s |
| K线主源 | akshare 东财 | 新浪直连（不封IP） |
| 财报fallback | 仅akshare | akshare + 新浪直连双保险 |
| data-sources.md | 旧优先级 | 对齐新优先级 |

## 致谢

- [UZI-Skill](https://github.com/wbh604/UZI-Skill) by FloatFu-true
- [a-stock-data](https://github.com/simonlin1212/a-stock-data) by simonlin1212

## License

MIT
