# RentFlow AI 数据模型规划

本文定义实体职责和关系，不替代 Alembic 迁移文件。字段细节在进入对应里程碑时再确认。

## 1. 实体关系概览

```text
User ──< SearchSession ──< AgentRun ──< ToolCall
  │            │                └──< Approval
  │            └──< SearchResult >── Listing
  ├──< Favorite >─────────────── Listing
  └──< Appointment >──────────── Listing

Listing ──< ListingEmbedding
Location ──< CommuteResult >──── Listing

KnowledgeDocument ──< KnowledgeChunk
EvaluationDataset ──< EvaluationCase
EvaluationRun ──< EvaluationResult
```

## 2. 身份与权限

### users

| 字段组 | 内容 |
|---|---|
| 身份 | id、email、password_hash |
| 状态 | status、email_verified |
| 资料 | display_name、avatar_url |
| 审计 | created_at、updated_at、last_login_at |

### roles / user_roles

角色初始定义：`tenant`、`operator`、`admin`。权限判断在服务端完成，模型不能决定用户角色。

### user_preferences

保存用户长期偏好，例如默认预算、常用工作地点、宠物和排序权重。与单次搜索条件分离。

## 3. 房源域

### listings

当前已实现。负责结构化房源事实：租金、户型、面积、状态、位置、日期、宠物政策和描述。位置层级拆分为行政区 `district` 与板块 `area`，避免“浦东新区”和“张江”等不同层级共用一个字段。

### listing_embeddings

| 字段 | 说明 |
|---|---|
| listing_id | 房源 ID |
| embedding | pgvector 向量 |
| model_name | Embedding 模型 |
| model_version | 模型/服务版本 |
| dimension | 向量维度 |
| content_hash | 参与向量化内容的哈希 |
| created_at | 生成时间 |

Embedding 不直接塞进 `listings`，便于模型升级、重建和多版本共存。

### favorites

用户与房源的多对多关系，`(user_id, listing_id)` 唯一。

### comparisons / comparison_items

保存用户的一次对比集合及 2～4 套候选房源，支持前端分享和恢复。

## 4. 地点与通勤域

### locations

| 字段组 | 内容 |
|---|---|
| 标识 | id、canonical_name、normalized_name |
| 分类 | district、area、location_type、is_active |
| 空间 | Geography(Point, 4326) |
| 来源 | source、source_id |

### location_aliases

地点别名单独存表，通过 `location_id` 指向标准地点，并对 `(location_id, normalized_alias)` 建立唯一约束。`normalized_alias` 可关联多个地点，用于表达“张江”等真实歧义；无法唯一匹配时返回候选，不自动猜测。

### commute_results

缓存地点/房源之间的路线结果：模式、时间、距离、Provider、计算时间、过期时间和是否估算。

## 5. 搜索与决策域

### search_sessions

保存一次可持续对话式找房会话：用户、原始输入、当前结构化条件、状态、版本和时间。

### search_results

保存一次搜索中的候选房源和排序信息：

- 硬条件是否满足；
- 空间和通勤结果；
- 软偏好得分；
- 总分和分项得分；
- 排名；
- 推荐证据；
- 未满足条件。

### constraint_relaxations

保存无结果诊断的建议：原条件、建议修改、预计新增候选数量、放宽成本和用户是否接受。

### ranking_profiles

保存默认或用户自定义的预算、通勤、偏好等权重。权重必须版本化，保证推荐可复现。

## 6. Agent 与审计域

### agent_runs

| 字段组 | 内容 |
|---|---|
| 关联 | user_id、search_session_id |
| 运行 | workflow_name、workflow_version、status |
| 模型 | provider、model、prompt_version |
| 成本 | input_tokens、output_tokens、estimated_cost |
| 追踪 | trace_id、started_at、completed_at |
| 错误 | error_code、error_summary |

### agent_steps

记录公开的工作流节点状态，不保存模型私有思维链。包括节点名、输入摘要、输出摘要、耗时与状态。

### tool_calls

记录工具名称、参数摘要、结果摘要、耗时、重试次数、是否产生副作用和错误类型。

### approvals

记录待审批操作、风险级别、请求人、审批人、决定、理由和时间。审批通过后仍需再次校验权限和业务状态。

### audit_events

记录登录、房源变更、预约、审批和管理操作。审计日志只追加，不由普通业务接口修改。

## 7. 预约域

### viewing_slots

运营方为房源提供的可预约时间段。

### appointments

包含用户、房源、时间段、状态、幂等键、备注和取消原因。

状态建议：

```text
pending_confirmation
confirmed
reschedule_requested
cancelled
completed
```

需要数据库唯一约束防止同一房源/时间段重复确认。

## 8. RAG 知识域

### knowledge_documents

保存文档元数据、版本、类型、来源、文件地址、哈希、状态、租户范围和发布时间。

### knowledge_chunks

| 字段 | 说明 |
|---|---|
| document_id | 所属文档 |
| chunk_index | 文档内顺序 |
| content | 清洗后的文本 |
| page_number | 页码 |
| section_title | 章节 |
| metadata | JSONB 元数据 |
| embedding | pgvector 向量 |
| token_count | 估算 Token 数 |
| content_hash | 去重与重建判断 |

### ingestion_jobs

记录上传、解析、分块、Embedding 和发布的异步任务状态及错误。

### knowledge_answers / answer_citations

保存生成回答和引用关系。引用必须能回到具体文档版本、Chunk、页码和原文片段。

## 9. 评测域

### evaluation_datasets / evaluation_cases

数据集类型：需求提取、房源检索、软偏好排序、RAG 问答、工具调用和端到端任务。

### evaluation_runs / evaluation_results

记录代码版本、Prompt 版本、模型版本、指标、单案例结果、失败分类、成本和耗时。

## 10. 数据生命周期

| 数据 | 保留策略 |
|---|---|
| 房源 | 软下架，保留历史状态 |
| 搜索会话 | 用户可删除；日志按策略脱敏 |
| Agent Run | 保留摘要和指标，敏感输入可脱敏/过期 |
| Tool Call | 保留审计摘要，不保存密钥 |
| 文档 | 版本化，发布版本不可直接覆盖 |
| Embedding | 可按模型版本重建 |
| 审批/审计 | 只追加并设置较长保留周期 |

## 11. 实施顺序

```text
已完成：listings
M2：search_sessions（可先以内存/响应实现，闭环后落库）
M3：locations、commute_results、listing_embeddings、ranking_profiles
M4：knowledge_documents、knowledge_chunks、ingestion_jobs、citations
M5：agent_runs、agent_steps、tool_calls、approvals
M6：users、roles、favorites、appointments、audit_events
M7：evaluation_* 与长期监控数据
```

