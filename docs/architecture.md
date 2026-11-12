# RentFlow AI 总体架构

## 1. 产品边界

RentFlow AI 由三个产品面组成：

```text
租客端房源网站
运营管理平台
Agent 决策与知识引擎
```

租客端负责找房、地图、对比与预约；运营端负责房源、文档、Agent 运行和评测；Agent 引擎负责需求解析、检索编排、解释、澄清和受控工具调用。

## 2. 系统上下文

```text
租客 / 运营 / 管理员
        ↓
Vue 3 Web
        ↓ HTTP / SSE
FastAPI 模块化单体
        ├── PostgreSQL / PostGIS / pgvector
        ├── DeepSeek
        ├── Map Provider
        ├── Redis / Celery
        ├── MinIO
        └── OpenTelemetry / Langfuse
```

MVP 使用模块化单体，不拆微服务。只有出现独立发布、独立扩缩容或明确故障隔离需求时才拆分。

## 3. 后端模块

| 模块 | 职责 | 不负责 |
|---|---|---|
| `auth` | 登录、令牌、用户身份、RBAC | 业务权限规则本身 |
| `users` | 用户资料、偏好、角色关联 | 模型记忆 |
| `listings` | 房源 CRUD、状态、结构化与空间查询 | 自然语言解析 |
| `locations` | 上海地点目录、标准化、坐标解析 | 房源推荐 |
| `commute` | 通勤 Provider、路线与时间计算 | 决定推荐权重 |
| `search` | 需求提取、条件映射、检索编排 | 直接实现数据库细节 |
| `ranking` | 多目标评分、权重、约束松弛 | 生成无依据的解释 |
| `knowledge` | 文档摄取、Chunk、RAG、引用 | 房源硬条件筛选 |
| `agents` | LangGraph 状态、节点、工具编排 | 绕过业务 Service |
| `appointments` | 带看时间、冲突、确认、取消 | 由模型直接写数据库 |
| `audit` | Agent Run、工具调用、审计事件 | 保存密钥和敏感原文 |
| `evaluations` | 数据集、评测运行、指标与失败案例 | 在线业务执行 |

## 4. 分层规则

```text
Router
  → Application Service
    → Domain/Business Service
      → Repository / Provider
```

- Router：HTTP 参数、状态码、响应模型；
- Service：业务流程、事务边界、权限判断；
- Repository：SQLAlchemy 与数据库查询；
- Provider：DeepSeek、地图、Embedding、对象存储等外部系统；
- LangGraph：编排已有 Service 和 Tool，不复制业务逻辑；
- MCP：包装已有 Service，不把业务逻辑写进 handler。

## 5. 核心搜索流程

```text
用户自然语言
  → DeepSeek 提取 RentalRequirements
  → Pydantic 验证
  → 检查关键条件是否缺失
  → 地点标准化与坐标解析
  → SQL 硬条件筛选
  → PostGIS 空间筛选
  → 通勤计算
  → pgvector 软偏好召回/排序
  → 多目标评分
  → 无结果诊断或推荐解释
  → 返回结果、证据和未满足条件
```

## 6. RAG 架构

RAG 用于租赁知识，不替代房源数据库查询。

```text
文档上传
  → 文件存储
  → 解析与清洗
  → 分块与元数据
  → Embedding
  → pgvector
  → 关键词/向量混合召回
  → Rerank
  → DeepSeek 带引用生成
```

首批知识类型：租赁 FAQ、入住/退租规则、演示合同、报修手册。所有回答必须包含引用；无证据时应拒绝生成确定性结论。

## 7. Agent 与多 Agent 原则

### MVP

MVP 使用单个显式 LangGraph 工作流加工具，不使用自由对话式多 Agent。

### 可选后期结构

```text
Supervisor
  ├── Finding Agent：找房决策
  ├── Viewing Agent：带看与路线
  └── Support Agent：租后知识与工单
```

只有满足以下条件才拆 Agent：

1. 业务目标明显不同；
2. 工具与权限集合不同；
3. 上下文和 Prompt 明显不同；
4. 需要独立评测；
5. 可以清晰定义状态交接协议。

多 Agent 不是项目创新点。项目创新重点是可解释多约束决策、约束冲突诊断和可重复评测。

## 8. 关键架构决策

| 决策 | 选择 | 原因 |
|---|---|---|
| 应用形态 | 模块化单体 | 降低早期分布式复杂度 |
| 前端形态 | 一个 Vue 应用、两个 Layout | 共享组件、类型和权限逻辑 |
| 硬条件 | SQL/Pydantic | 保证确定性和可审计 |
| 空间查询 | PostGIS | 空间索引和米制距离 |
| 软偏好 | pgvector | 处理非结构化语义偏好 |
| LLM | DeepSeek Provider | 通过接口隔离厂商 |
| Agent | LangGraph | 显式状态、暂停恢复、可观测 |
| RAG | 自建检索管线 | 能解释、评测并控制权限 |
| 工具标准 | MCP 后置 | 先稳定 Service，再标准化暴露 |

## 9. 创新能力

### 多约束决策

硬条件零违规，空间、通勤和软偏好分别计算，避免单一相似度决定结果。

### 约束松弛

无结果时计算最小调整方案，例如预算增加、通勤放宽或户型调整，必须由用户确认后重搜。

### 可解释排序

返回预算、通勤、偏好等分项得分、满足条件、未满足条件和证据来源。

### 可评测 Agent

评测条件提取、硬约束违规率、Recall@K、NDCG@K、引用准确率、工具成功率、成本和延迟。

