# RentFlow AI API 目录

## 1. 约定

- Base URL：`/api/v1`；
- 请求与响应：JSON，文件上传除外；
- 时间：ISO 8601，数据库使用带时区时间；
- 主键：UUID；
- 分页：MVP 使用 `limit + offset`，高数据量模块后续使用 cursor；
- 错误响应：统一包含 `code`、`message`、`request_id` 和可选 `details`；
- 认证：`Bearer <access_token>`；
- SSE：Agent 长任务使用独立事件流接口；
- 幂等：预约等写操作使用 `Idempotency-Key` 请求头。

## 2. 实现状态

| 标记 | 含义 |
|---|---|
| 已完成 | 已实现并通过当前阶段测试 |
| 开发中 | 已有部分代码，尚未完成里程碑验收 |
| 待开发 | 已规划且处于 MVP 范围 |
| 暂缓 | MVP 后再实现 |

## 3. System

| 方法 | 路径 | 认证 | 功能 | 状态 |
|---|---|---|---|---|
| GET | `/health` | 无 | API 进程存活检查 | 已完成 |
| GET | `/health/ready` | 无 | 数据库等依赖就绪检查 | 已完成 |
| GET | `/version` | 无 | 构建版本、提交号和环境信息 | 待开发 |

## 4. Auth 与用户

| 方法 | 路径 | 认证/角色 | 功能 | 状态 |
|---|---|---|---|---|
| POST | `/auth/register` | 无 | 注册租客账户 | 待开发 |
| POST | `/auth/login` | 无 | 登录并签发访问/刷新令牌 | 待开发 |
| POST | `/auth/refresh` | Refresh Token | 刷新访问令牌 | 待开发 |
| POST | `/auth/logout` | 用户 | 使刷新令牌失效 | 待开发 |
| GET | `/users/me` | 用户 | 当前用户资料 | 待开发 |
| PATCH | `/users/me` | 用户 | 修改个人资料 | 待开发 |
| GET | `/users/me/preferences` | 租客 | 获取找房偏好 | 待开发 |
| PUT | `/users/me/preferences` | 租客 | 保存找房偏好 | 待开发 |

## 5. 房源 Listings

| 方法 | 路径 | 认证/角色 | 功能 | 状态 |
|---|---|---|---|---|
| GET | `/listings` | 无 | 条件、空间和分页搜索 | 已完成 |
| GET | `/listings/{listing_id}` | 无 | 房源详情 | 已完成 |
| POST | `/listings` | 运营 | 创建房源 | 已完成基础能力，待加权限 |
| PATCH | `/listings/{listing_id}` | 运营 | 修改房源 | 待开发 |
| POST | `/listings/{listing_id}/publish` | 运营 | 上架房源 | 待开发 |
| POST | `/listings/{listing_id}/offline` | 运营 | 下架房源 | 待开发 |
| DELETE | `/listings/{listing_id}` | 管理员 | 软删除房源 | 暂缓 |
| POST | `/listings/imports` | 运营 | 创建批量导入任务 | 暂缓 |
| GET | `/listings/imports/{job_id}` | 运营 | 查询导入状态 | 暂缓 |

### GET `/listings` 查询能力

| 参数组 | 参数 | 说明 |
|---|---|---|
| 硬条件 | `district` | 行政区，例如浦东新区 |
| 硬条件 | `area` | 行政区下属板块，例如张江 |
| 硬条件 | `max_rent` | 最高月租 |
| 硬条件 | `bedrooms` | 卧室数 |
| 硬条件 | `pets_allowed` | 是否允许宠物 |
| 硬条件 | `available_before` | 最晚入住日期 |
| 空间条件 | `longitude` | 参考点经度 |
| 空间条件 | `latitude` | 参考点纬度 |
| 空间条件 | `radius_m` | 搜索半径，米 |
| 分页 | `limit` | 返回数量，上限 100 |
| 分页 | `offset` | 偏移量 |

## 6. 智能搜索 Search

| 方法 | 路径 | 认证 | 功能 | 状态 |
|---|---|---|---|---|
| POST | `/search/requirements` | 可匿名 | 自然语言转结构化需求 | 已完成 |
| POST | `/search/listings` | 可匿名 | 自然语言解析并查询房源 | 已完成 |
| POST | `/search/listings/confirmed` | 可匿名 | 使用用户已确认的结构化条件查询，不再次调用 LLM | 已完成 |
| POST | `/search/sessions` | 租客/匿名会话 | 创建搜索会话 | 待开发 |
| GET | `/search/sessions/{session_id}` | 会话所有者 | 获取搜索状态与条件 | 待开发 |
| POST | `/search/sessions/{session_id}/messages` | 会话所有者 | 补充或修改需求 | 待开发 |
| POST | `/search/sessions/{session_id}/relaxations` | 会话所有者 | 接受某个约束放宽建议 | 待开发 |
| GET | `/search/sessions/{session_id}/events` | 会话所有者 | SSE 获取 Agent 进度 | 待开发 |
| GET | `/search/sessions/{session_id}/results` | 会话所有者 | 获取最终推荐列表 | 待开发 |

### 自然语言搜索响应应包含

| 字段 | 含义 |
|---|---|
| `requirements` | 模型提取并验证后的条件 |
| `applied_filters` | 实际执行的硬条件和空间条件 |
| `unresolved_requirements` | 尚未执行的条件 |
| `results` | 候选房源 |
| `relaxation_suggestions` | 无结果时的可选放宽方案 |
| `trace_id` | 本次搜索追踪 ID |

## 7. 地点与通勤

| 方法 | 路径 | 认证 | 功能 | 状态 |
|---|---|---|---|---|
| GET | `/locations/search` | 无 | 搜索上海地点目录 | 已完成 |
| GET | `/locations/{location_id}` | 无 | 地点详情与坐标 | 已完成 |
| POST | `/locations/resolve` | 无 | 文本地点标准化与歧义候选 | 已完成 |
| POST | `/commutes/estimate` | 用户 | 估算单条通勤 | 待开发 |
| POST | `/commutes/batch` | 内部 | 批量计算候选房源通勤 | 待开发 |

## 8. 排序、对比与收藏

| 方法 | 路径 | 认证 | 功能 | 状态 |
|---|---|---|---|---|
| POST | `/rankings/preview` | 用户 | 根据权重重新排序候选房源 | 待开发 |
| POST | `/comparisons` | 租客 | 创建房源对比集合 | 待开发 |
| GET | `/comparisons/{comparison_id}` | 所有者 | 获取对比结果 | 待开发 |
| POST | `/favorites/{listing_id}` | 租客 | 收藏房源 | 待开发 |
| DELETE | `/favorites/{listing_id}` | 租客 | 取消收藏 | 待开发 |
| GET | `/favorites` | 租客 | 收藏列表 | 待开发 |

## 9. 带看预约

| 方法 | 路径 | 认证/角色 | 功能 | 状态 |
|---|---|---|---|---|
| GET | `/listings/{listing_id}/viewing-slots` | 租客 | 可预约时间段 | 待开发 |
| POST | `/appointments` | 租客 | 创建待确认预约 | 待开发 |
| GET | `/appointments` | 用户 | 查询自己的预约 | 待开发 |
| GET | `/appointments/{appointment_id}` | 相关用户 | 预约详情 | 待开发 |
| POST | `/appointments/{appointment_id}/confirm` | 运营/租客确认链 | 确认预约 | 待开发 |
| POST | `/appointments/{appointment_id}/reschedule` | 相关用户 | 改期 | 待开发 |
| POST | `/appointments/{appointment_id}/cancel` | 相关用户 | 取消预约 | 待开发 |

## 10. 知识库与 RAG

| 方法 | 路径 | 认证/角色 | 功能 | 状态 |
|---|---|---|---|---|
| POST | `/knowledge/documents` | 运营 | 上传文档 | 待开发 |
| GET | `/knowledge/documents` | 运营 | 文档列表 | 待开发 |
| GET | `/knowledge/documents/{document_id}` | 运营 | 文档与处理状态 | 待开发 |
| POST | `/knowledge/documents/{document_id}/ingest` | 运营 | 创建解析与向量化任务 | 待开发 |
| POST | `/knowledge/documents/{document_id}/publish` | 运营 | 发布知识版本 | 待开发 |
| POST | `/knowledge/search` | 内部/运营 | 调试知识检索 | 待开发 |
| POST | `/knowledge/answers` | 用户 | 生成带引用回答 | 待开发 |
| GET | `/knowledge/answers/{answer_id}` | 所有者 | 回答、引用和反馈 | 待开发 |
| POST | `/knowledge/answers/{answer_id}/feedback` | 用户 | 有用/无用反馈 | 待开发 |

## 11. Agent 运行与审批

| 方法 | 路径 | 认证/角色 | 功能 | 状态 |
|---|---|---|---|---|
| GET | `/agent-runs` | 运营 | Agent Run 列表 | 待开发 |
| GET | `/agent-runs/{run_id}` | 所有者/运营 | 节点、工具、耗时与状态 | 待开发 |
| GET | `/agent-runs/{run_id}/events` | 所有者/运营 | SSE 运行事件 | 待开发 |
| POST | `/agent-runs/{run_id}/cancel` | 所有者/运营 | 取消运行 | 待开发 |
| GET | `/approvals` | 运营 | 待审批操作列表 | 待开发 |
| POST | `/approvals/{approval_id}/approve` | 有权限用户 | 批准操作 | 待开发 |
| POST | `/approvals/{approval_id}/reject` | 有权限用户 | 拒绝操作 | 待开发 |

## 12. 运营、评测与监控

| 方法 | 路径 | 认证/角色 | 功能 | 状态 |
|---|---|---|---|---|
| GET | `/admin/dashboard` | 运营/管理员 | 核心业务与 Agent 指标 | 待开发 |
| GET | `/evaluations/datasets` | 运营 | 评测数据集列表 | 待开发 |
| POST | `/evaluations/datasets` | 运营 | 创建评测集 | 待开发 |
| POST | `/evaluations/runs` | 运营 | 启动离线评测 | 待开发 |
| GET | `/evaluations/runs/{run_id}` | 运营 | 评测指标和失败案例 | 待开发 |
| GET | `/audit-events` | 管理员 | 审计事件查询 | 待开发 |

## 13. 错误码规划

| 错误码 | HTTP | 场景 |
|---|---:|---|
| `VALIDATION_ERROR` | 422 | 请求或模型输出校验失败 |
| `RESOURCE_NOT_FOUND` | 404 | 房源、文档或预约不存在 |
| `AUTHENTICATION_REQUIRED` | 401 | 未登录或令牌无效 |
| `PERMISSION_DENIED` | 403 | 无权限执行操作 |
| `CONFLICT` | 409 | 预约冲突、状态冲突 |
| `IDEMPOTENCY_CONFLICT` | 409 | 同一幂等键对应不同请求 |
| `LLM_NOT_CONFIGURED` | 503 | 模型未配置 |
| `LLM_UPSTREAM_ERROR` | 502 | 模型超时或上游异常 |
| `LOCATION_UNRESOLVED` | 422 | 地点无法唯一解析 |
| `KNOWLEDGE_NOT_FOUND` | 404 | 无可引用知识证据 |
| `INTERNAL_ERROR` | 500 | 未分类内部异常 |

