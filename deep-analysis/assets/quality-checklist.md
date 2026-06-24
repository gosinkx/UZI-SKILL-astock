# Quality Checklist · 报告生成完毕后必须自检

每生成一份报告，Claude 必须按本清单逐项检查。任何 ❌ 都要返工。

## 数据完整性
- [ ] `raw_data.json` 包含 20 个 dimension key（0-19）
- [ ] 每个 key 都有 `data` / `source` / `fallback` 字段
- [ ] `dimensions.json` 包含 19 个维度评分（每个 1-10）
- [ ] `panel.json` 包含 **50** 个投资者 Signal
- [ ] `synthesis.json` 五段 dashboard 全部填充

## 投资者评审
- [ ] 50 个 Signal 的 `signal` 字段都是 `bullish/bearish/neutral` 之一
- [ ] 50 个 Signal 都有 `confidence` 0-100
- [ ] 22 位游资里至少 N 位返回 `不适合`（除非这只票真的什么都符合）
- [ ] 7 大流派每组都有 ≥ 1 个 `comment` 体现该流派语言风格
- [ ] 段永平的 comment 必须问到"生意/人/价格"三问之一
- [ ] 章盟主的 comment 必须出现"格局"或"趋势"
- [ ] 北京炒家的 comment 必须谈"首板"或"机构"

## The Great Divide
- [ ] `bull` 和 `bear` 都已选定
- [ ] 3 轮辩论每轮各有 `bull_say` 和 `bear_say`
- [ ] 每段 ≤ 80 字
- [ ] `punchline` 长度 20-30 字
- [ ] `punchline` 包含具体数字 + 反预期事实

## 禁用话术（违反必须重写）
- [ ] 报告中**没有**："基本面良好"
- [ ] 报告中**没有**："值得关注"
- [ ] 报告中**没有**："前景广阔"
- [ ] 报告中**没有**："建议重视"
- [ ] 报告中**没有**："存在一定风险"

## HTML / PNG 产物
- [ ] `full-report.html` 文件 > 30 KB
- [ ] HTML 在 Chrome 打开无 console error
- [ ] `share-card.png` 文件 > 200 KB（说明 DPI 够 + 截图成功）
- [ ] `war-report.png` 文件 > 200 KB
- [ ] `one-liner.txt` 长度 ≤ 200 字

## 安全维度
- [ ] 杀猪盘评级永远存在（即使 🟢 安全也要写出来）
- [ ] 8 信号每个都有"命中 / 未命中 / 数据不足"标签
- [ ] 风险清单至少 1 条（即使所有维度都很好）

## 用户提示
- [ ] 完成后向用户输出：报告路径 + 综合评分 + 一句话定调 + trap level
- [ ] 不在 Claude 的回答里**复述**整份报告——只指路 + 关键数字
