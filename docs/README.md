# RentFlow AI 文档中心

本目录是 RentFlow AI 的产品与研发基线。开发前先确认需求编号、模块边界和当前里程碑，避免边写边扩展范围。

## 文档索引

| 文档 | 作用 | 主要读者 |
|---|---|---|
| [requirements.md](requirements.md) | 产品目标、功能需求、非功能需求、MVP 定义 | 产品、前后端、测试 |
| [architecture.md](architecture.md) | 系统边界、模块划分、核心流程、多 Agent 原则 | 后端、架构、面试准备 |
| [api-catalog.md](api-catalog.md) | 前后端接口目录、权限、实现状态 | 前端、后端、测试 |
| [data-model.md](data-model.md) | 核心实体、表职责、关系与生命周期 | 后端、数据库 |
| [frontend-plan.md](frontend-plan.md) | 租客端与运营端页面、组件、状态和迭代顺序 | 前端、产品 |
| [development-roadmap.md](development-roadmap.md) | 分阶段开发任务、依赖关系、验收标准 | 项目开发者 |
| [engineering-issues.md](engineering-issues.md) | 重大工程问题、解决方案、预防清单与面试复盘 | 项目开发者、面试准备 |

## 阅读顺序

第一次了解项目：

```text
requirements
  → architecture
  → frontend-plan
  → api-catalog
  → data-model
  → development-roadmap
```

开始一个开发任务：

```text
确认当前里程碑
  → 找到对应 FR 编号
  → 检查 API 和数据模型
  → 实现最小闭环
  → 测试验收
  → 更新实现状态
```

## 状态定义

| 状态 | 含义 |
|---|---|
| 规划中 | 已进入需求，但尚未进入当前里程碑 |
| 待开发 | 前置条件满足，可以开始 |
| 开发中 | 当前正在实现 |
| 待验收 | 功能完成，等待测试与文档确认 |
| 已完成 | 已满足验收标准 |
| 暂缓 | 有意延后，不阻塞当前里程碑 |

## 当前基线

- 当前里程碑：M3 决策检索与通勤计算；
- 已完成：M0～M2 后端能力、F0 前端基础、F1 自然语言解析—确认—确定性搜索闭环；
- 已完成：F2.1 独立搜索结果页与 URL 分页、F2.2 房源详情页及异常状态测试；
- 已完成：M3.1 上海标准地点目录、别名解析、歧义候选与地点 API；
- 已完成：F2.3 MapLibre 桌面端分栏、房源联动、移动端列表/地图切换与异步分包；
- 已完成：M3.2A 通勤 Provider 协议、四种交通方式和可解释的本地估算；
- 已完成：M3.2B 通勤缓存模型、约束、索引及可升级回滚的数据库迁移；
- 已完成：M3.2C 稳定请求指纹、原子 Upsert Repository、单条缓存 Service 与生命周期测试；
- 当前目标：实现 M3.2D 房源到标准地点的批量通勤计算与 API；
- 下一里程碑：M3 上海地点目录、通勤计算、软偏好检索与多目标排序；
- 当前不做：多 Agent、预约、认证、完整 RAG 管理后台。

