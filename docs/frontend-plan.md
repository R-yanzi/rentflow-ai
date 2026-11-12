# RentFlow AI 前端规划

## 1. 前端形态

第一阶段使用一个 Vue 3 + TypeScript 项目，通过两个 Layout 提供租客端与运营端。

```text
src/
├── layouts/
│   ├── TenantLayout.vue
│   └── AdminLayout.vue
├── modules/
│   ├── auth/
│   ├── listings/
│   ├── search/
│   ├── comparison/
│   ├── appointments/
│   ├── knowledge/
│   ├── agent-runs/
│   └── evaluations/
├── shared/
│   ├── api/
│   ├── components/
│   ├── composables/
│   ├── stores/
│   └── types/
└── router/
```

## 2. 租客端页面

| 页面 | 路由 | 核心功能 | 阶段 |
|---|---|---|---|
| 首页 | `/` | 产品入口、示例需求、热门区域 | F1 |
| 智能找房 | `/search` | 自然语言输入、条件预览、Agent 进度 | F1 |
| 搜索结果 | `/search/:sessionId/results` | 列表/地图、筛选、排序、未满足条件 | F2 |
| 房源详情 | `/listings/:id` | 房源事实、地图、通勤、推荐解释 | F2 |
| 房源对比 | `/compare/:id` | 2～4 套房源并排对比、权重模拟 | F3 |
| 收藏 | `/favorites` | 收藏房源 | F4 |
| 预约 | `/appointments` | 预约、改期、取消、状态 | F5 |
| 知识助手 | `/knowledge` | 租赁问答、引用来源 | F4 |
| 个人中心 | `/profile` | 资料、默认偏好、历史搜索 | F5 |

## 3. 运营管理端页面

| 页面 | 路由 | 核心功能 | 阶段 |
|---|---|---|---|
| 登录 | `/admin/login` | 运营登录 | F5 |
| 数据看板 | `/admin` | 房源、搜索、Agent、成本指标 | F6 |
| 房源管理 | `/admin/listings` | 列表、筛选、上下架 | F3 |
| 房源编辑 | `/admin/listings/:id` | 表单、地图选点、状态管理 | F3 |
| 预约管理 | `/admin/appointments` | 审核、冲突、改期 | F5 |
| 知识库 | `/admin/knowledge` | 上传、版本、摄取状态 | F4 |
| Agent Runs | `/admin/agent-runs` | 节点、工具、耗时、错误 | F4 |
| Prompt/评测 | `/admin/evaluations` | 数据集、运行、指标、失败案例 | F6 |
| 审批中心 | `/admin/approvals` | 高风险操作审批 | F5 |
| 用户与权限 | `/admin/users` | 用户、角色和状态 | F6 |

## 4. 核心页面结构

### 4.1 智能找房页

```text
自然语言输入
  ↓
已提取条件 Chips
  ↓
缺失/冲突条件提示
  ↓
开始搜索按钮
  ↓
公开的 Agent 执行进度
```

条件 Chip 可编辑，但每次修改需要明确区分“用户输入”和“模型提取”。

### 4.2 搜索结果页

桌面端使用列表和地图分栏：

```text
┌──────────────────────────────────────────────┐
│ 搜索摘要 / 条件 / 排序 / 保存搜索            │
├──────────────────────┬───────────────────────┤
│ 房源列表              │ MapLibre 地图          │
│ 匹配得分和理由         │ 标记、范围圈、路线      │
│ 未满足条件             │                       │
└──────────────────────┴───────────────────────┘
```

移动端使用地图/列表切换，不强制分栏。

### 4.3 房源详情页

- 房源基本事实；
- 地理位置和周边；
- 通勤时间与计算来源；
- 匹配得分拆解；
- 满足和未满足条件；
- 推荐证据；
- 收藏、对比、预约入口；
- “合成数据”明显标识。

### 4.4 Agent Run 页面

只展示可公开执行事件：

```text
需求解析完成
地点解析完成
硬条件筛选：301 → 42
通勤计算：42 → 18
软偏好排序完成
推荐解释生成完成
```

不展示模型私有思维链。

## 5. 共享组件

| 组件 | 用途 |
|---|---|
| `RequirementInput` | 自然语言输入与示例 |
| `RequirementChips` | 展示和编辑结构化条件 |
| `ListingCard` | 房源摘要、得分、匹配理由 |
| `ListingMap` | MapLibre 标记和交互 |
| `ScoreBreakdown` | 多目标得分拆解 |
| `ConstraintBadge` | 满足/未满足/未处理条件 |
| `AgentTimeline` | SSE 执行进度 |
| `CitationPanel` | RAG 引用和原文定位 |
| `EmptyResultDiagnosis` | 无结果诊断与放宽建议 |
| `ApprovalDialog` | 高风险操作确认 |

## 6. 前端状态划分

| 状态 | 管理方式 |
|---|---|
| 登录用户、主题、全局偏好 | Pinia |
| API 请求与缓存 | TanStack Query for Vue 或轻量封装 |
| 页面临时表单 | 组件状态 |
| Agent SSE 事件 | 专用 composable/store |
| 地图视口和选中房源 | 搜索页局部 store |
| URL 可分享筛选条件 | Vue Router Query |

不要把所有服务端数据复制到 Pinia，避免双重数据源。

## 7. 前端模块实施顺序

### F0 工程基础

Vue、TypeScript、Vite、Element Plus、Router、Pinia、Axios、代码检查和 API 基础封装。

### F1 搜索闭环

首页、智能找房、结构化条件预览、调用自然语言搜索 API。

### F2 列表与地图

搜索结果、分页、MapLibre、房源详情、距离展示。

### F3 决策体验

房源对比、评分拆解、无结果诊断、What-if 权重调整、运营房源管理。

### F4 Agent 与 RAG

Agent Timeline、知识助手、引用面板、Agent Run 查看。

### F5 账户与预约

登录、个人中心、收藏、预约、运营审批。

### F6 企业展示

看板、评测管理、权限、错误监控和完整端到端测试。

## 8. UX 约束

- 所有房源明确标注“演示合成数据”；
- 模型提取结果必须允许用户修改；
- 未处理条件必须可见；
- 无结果不能只显示空白页；
- RAG 回答必须显示引用；
- 长任务必须显示进度、取消和失败恢复入口；
- 高风险操作必须显示影响范围并二次确认；
- 地图服务失败时仍可使用列表模式。

