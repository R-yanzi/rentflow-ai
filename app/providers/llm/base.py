"""大语言模型 Provider 抽象接口。"""

from typing import Protocol, TypeVar

from pydantic import BaseModel

StructuredModel = TypeVar(
    "StructuredModel",
    bound=BaseModel,
)


class LLMProvider(Protocol):
    """结构化大模型调用接口。

    业务层只依赖此协议，不直接依赖 OpenAI、通义千问或其他厂商 SDK。
    """

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[StructuredModel],
    ) -> StructuredModel:
        """让模型按照指定 Pydantic 模型返回结构化结果."""
        ...
