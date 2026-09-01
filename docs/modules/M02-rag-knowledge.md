# M02 — RAG 知识库

| 属性 | 值 |
|------|-----|
| **模块 ID** | M02 |
| **优先级** | P0 |
| **里程碑** | MS2（W3） |
| **状态** | `blocked` |
| **依赖** | M01 |

---

## 1. 目标

构建本地 RAG 知识库，支撑 rules_agent 检索平台规则、产品资料与运营 SOP。

## 2. 知识库内容规划（首期）

| 分类 | 来源 | 格式 |
|------|------|------|
| Amazon Listing 规范 | 官方卖家中心文档（公开摘录） | Markdown |
| TikTok Shop 商品规范 | 官方文档摘录 | Markdown |
| 示例产品资料 | 公开参数、说明书摘要 | PDF/MD |
| 优秀 Listing 范例 | 人工标注 10–20 条 | JSON |
| 运营 SOP | 自建：上架检查清单 | Markdown |

**禁止入库：** 公司内部未公开价格、供应商、未授权店铺数据。

## 3. 交付物

- [ ] `knowledge/` 目录结构与 ingest 规范
- [ ] 文档解析器：PDF、MD、JSON
- [ ] 分块策略：RecursiveCharacterTextSplitter，chunk_size=512，overlap=64
- [ ] Chroma 本地持久化（`data/chroma/`）
- [ ] 检索 API：`POST /api/v1/knowledge/search`
- [ ] 管理 API：文档上传、重建索引、删除
- [ ] Ingest CLI：`python -m scripts.ingest_knowledge`

## 4. 技术规范

### 4.1 检索参数

| 参数 | 默认值 |
|------|--------|
| top_k | 5 |
| score_threshold | 0.7（可配置） |
| 混合检索 | Phase 2 可选，首期纯向量 |

### 4.2 Embedding

- 通过 `LLMProvider.embed()` 或独立 `EmbeddingProvider`
- 向量维度与模型绑定，变更需全量 re-index

### 4.3 元数据字段

```json
{
  "doc_id": "uuid",
  "category": "amazon_rules | product | sop | example",
  "platform": "amazon | tiktok | general",
  "source_file": "path",
  "version": "1.0",
  "updated_at": "iso8601"
}
```

## 5. 验收标准

1. ingest 全部首期文档，索引 > 0 条
2. 测试查询集 20 题，人工判定相关率 ≥ 80%
3. 检索 API p95 延迟 < 500ms（本地）
4. 重建索引命令可重复执行（幂等）

## 6. 不在本模块范围

- Agent 内如何消费检索结果（M03 rules_agent）
- 前端知识库 UI（M05，MS5 实现）
