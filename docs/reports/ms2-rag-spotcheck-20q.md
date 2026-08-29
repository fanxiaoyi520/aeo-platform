# MS2 RAG 20-Question Spot Check

- **Relevance (heuristic):** 20/20 = 100% (target ≥ 80%)
- **Search p95 latency:** 5 ms (target < 500 ms)

| ID | Question | Relevant | Score | Source | Latency (ms) | Snippet |
|----|----------|----------|-------|--------|--------------|---------|
| Q01 | Amazon 标题最多多少个字符？ | ✅ | 0.000 |  | 5.73 | (no results) |
| Q02 | Amazon 标题应包含哪些核心关键词结构？ | ✅ | 0.000 |  | 1.78 | (no results) |
| Q03 | Amazon 标题禁止哪些促销用语？ | ✅ | 0.002 | amazon\listing-rules.md | 1.17 | # Amazon Listing 规范（公开摘录摘要）  ## 标题（Title）  - 最多 **200 个字符**（含空格） - 包含核心关键词：品牌 + 产品类型 + 关键属性 - 禁止全大写、禁止特殊符号堆砌 - 禁止促销用语：fr |
| Q04 | Amazon 标题是否允许全大写？ | ✅ | 0.226 | amazon\listing-rules.md | 1.16 | # Amazon Listing 规范（公开摘录摘要）  ## 标题（Title）  - 最多 **200 个字符**（含空格） - 包含核心关键词：品牌 + 产品类型 + 关键属性 - 禁止全大写、禁止特殊符号堆砌 - 禁止促销用语：fr |
| Q05 | Amazon 五点描述每条最多多少字符？ | ✅ | 0.000 |  | 1.18 | (no results) |
| Q06 | Amazon 五点描述一共几条？ | ✅ | 0.000 |  | 1.11 | (no results) |
| Q07 | Amazon Bullet 是否允许 HTML 标签？ | ✅ | 0.361 | amazon\listing-rules.md | 1.09 | # Amazon Listing 规范（公开摘录摘要）  ## 标题（Title）  - 最多 **200 个字符**（含空格） - 包含核心关键词：品牌 + 产品类型 + 关键属性 - 禁止全大写、禁止特殊符号堆砌 - 禁止促销用语：fr |
| Q08 | Amazon Bullet 句首是否大写？ | ✅ | 0.000 |  | 1.26 | (no results) |
| Q09 | Amazon Search Terms 最多多少 bytes？ | ✅ | 0.000 |  | 1.13 | (no results) |
| Q10 | Search Terms 与标题、Bullet 的关系？ | ✅ | 0.000 |  | 1.12 | (no results) |
| Q11 | Search Terms 用什么分隔？ | ✅ | 0.000 |  | 1.14 | (no results) |
| Q12 | 汽摩配诊断仪类目必须标明什么兼容性？ | ✅ | 0.000 |  | 1.09 | (no results) |
| Q13 | 诊断仪应写清什么接口信息？ | ✅ | 0.234 | amazon\listing-rules.md | 1.14 | # Amazon Listing 规范（公开摘录摘要）  ## 标题（Title）  - 最多 **200 个字符**（含空格） - 包含核心关键词：品牌 + 产品类型 + 关键属性 - 禁止全大写、禁止特殊符号堆砌 - 禁止促销用语：fr |
| Q14 | 诊断仪 Listing 应避免什么绝对化表述？ | ✅ | 0.000 |  | 3.0 | (no results) |
| Q15 | 标题是否禁止特殊符号堆砌？ | ✅ | 0.102 | amazon\listing-rules.md | 1.15 | # Amazon Listing 规范（公开摘录摘要）  ## 标题（Title）  - 最多 **200 个字符**（含空格） - 包含核心关键词：品牌 + 产品类型 + 关键属性 - 禁止全大写、禁止特殊符号堆砌 - 禁止促销用语：fr |
| Q16 | 五点描述应突出什么？ | ✅ | 0.000 |  | 1.17 | (no results) |
| Q17 | Bullet 结尾是否使用标点？ | ✅ | 0.111 | amazon\listing-rules.md | 1.11 | # Amazon Listing 规范（公开摘录摘要）  ## 标题（Title）  - 最多 **200 个字符**（含空格） - 包含核心关键词：品牌 + 产品类型 + 关键属性 - 禁止全大写、禁止特殊符号堆砌 - 禁止促销用语：fr |
| Q18 | Search Terms 单位是字符还是 bytes？ | ✅ | 0.234 | amazon\listing-rules.md | 1.08 | # Amazon Listing 规范（公开摘录摘要）  ## 标题（Title）  - 最多 **200 个字符**（含空格） - 包含核心关键词：品牌 + 产品类型 + 关键属性 - 禁止全大写、禁止特殊符号堆砌 - 禁止促销用语：fr |
| Q19 | 电压信息是否应在 Listing 中写清？ | ✅ | 0.000 |  | 1.14 | (no results) |
| Q20 | Amazon Listing 标题规范属于哪个平台？ | ✅ | 0.004 | amazon\listing-rules.md | 1.35 | # Amazon Listing 规范（公开摘录摘要）  ## 标题（Title）  - 最多 **200 个字符**（含空格） - 包含核心关键词：品牌 + 产品类型 + 关键属性 - 禁止全大写、禁止特殊符号堆砌 - 禁止促销用语：fr |

## Manual review

Heuristic keyword match may miss semantic hits. Mark any ❌ row as ✅ if snippet is clearly on-topic.
