# Embedding 模型选型与评测

## 1. 目标

为中文租房软偏好检索选择可版本化、可复现的 Embedding 模型，并在确定模型输出维度后再创建 pgvector 字段。

## 2. 当前职责边界

- DeepSeek 负责自然语言需求理解和结构化提取；
- 独立 Embedding Provider 负责文本向量化；
- 检索质量使用版本化数据集、Recall@K 和 MRR 衡量；
- 不能仅凭公开排行榜决定生产模型。

截至 2026-11-18，DeepSeek 官方 API 文档未公开 Embedding 端点，因此项目不假设 DeepSeek 对话 API 可以生成可用向量。

## 3. 第一轮候选

| 模型 | 主要能力 | 最大稠密维度 | 第一轮定位 |
|---|---|---:|---|
| `Qwen/Qwen3-Embedding-0.6B` | 中文/多语言、指令感知、MRL 自定义维度 | 1024 | 重点评测 512、768、1024 维的质量与成本 |
| `BAAI/bge-m3` | 中文/多语言、稠密/稀疏/多向量检索 | 1024 | 作为成熟中文多语言检索基线 |

本机具有 NVIDIA GeForce RTX 3050 Ti Laptop GPU（4GB 显存），第一轮优先本地离线评测，不把外部 API 可用性混入质量比较。

## 4. 第一轮指标

- `Recall@3 = 1.0`：每条查询的相关房源必须进入前三；
- `MRR >= 0.9`：第一个相关结果应尽量靠前；
- 记录模型名称、输出维度、数据集版本、运行时间和运行设备；
- 同一模型和维度必须能够重复运行并得到稳定排名。

当前 `soft-preference-v1` 规模较小，只用于候选模型相对比较，不能代表线上真实质量。模型接入后需要继续加入同义表达、否定表达和困难负例。

## 5. 决策顺序

```text
统一 Provider
→ 相同数据集生成向量
→ 余弦相似度排名
→ Recall@3 / MRR
→ 比较延迟、显存和维度
→ 确定模型版本与维度
→ 创建 pgvector 迁移
```

## 6. 参考资料

- DeepSeek API：<https://api-docs.deepseek.com/api/deepseek-api/>
- Qwen3 Embedding：<https://huggingface.co/Qwen/Qwen3-Embedding-0.6B>
- BGE-M3：<https://huggingface.co/BAAI/bge-m3>
