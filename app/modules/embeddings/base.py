"""Embedding Provider 公共协议。"""

from typing import Protocol


class EmbeddingProvider(Protocol):
    """文本向量化 Provider。

    业务层只依赖该协议，不直接依赖 Transformers、
    FlagEmbedding 或某一家云端 API。
    """

    # 名称必须包含模型和版本，便于向量版本追踪。
    model_name: str

    # 数据库向量字段必须与 Provider 输出维度一致。
    dimension: int

    async def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """按输入顺序返回文本向量。"""
        ...
