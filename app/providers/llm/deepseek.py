"""DeepSeek 结构化输出 Provider。"""

import json
from json import JSONDecodeError
from typing import TypeVar

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
)
from pydantic import BaseModel, ValidationError

from app.providers.llm.exceptions import (
    LLMEmptyResponseError,
    LLMInvalidResponseError,
    LLMTimeoutError,
    LLMUpstreamError,
)

StructuredModel = TypeVar(
    "StructuredModel",
    bound=BaseModel,
)


class DeepSeekProvider:
    """通过 OpenAI-compatible API 调用 DeepSeek。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        max_tokens: int,
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )
        self._model = model
        self._max_tokens = max_tokens

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[StructuredModel],
    ) -> StructuredModel:
        """调用 JSON Output，并使用 Pydantic 验证最终结果。"""

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                # DeepSeek Chat Completions 当前使用 JSON Object 模式。
                response_format={"type": "json_object"},
                max_tokens=self._max_tokens,
                # 信息提取任务强调稳定性，不需要较高随机性。
                temperature=0,
            )
        except APITimeoutError as exc:
            raise LLMTimeoutError("DeepSeek request timed out") from exc
        except APIConnectionError as exc:
            raise LLMUpstreamError("Could not connect to DeepSeek") from exc
        except APIStatusError as exc:
            raise LLMUpstreamError(f"DeepSeek returned HTTP {exc.status_code}") from exc
        except APIError as exc:
            raise LLMUpstreamError("DeepSeek API request failed") from exc

        content = response.choices[0].message.content

        # DeepSeek 官方文档指出，JSON Output 失败时可能返回空白内容。
        if content is None or not content.strip():
            raise LLMEmptyResponseError("DeepSeek returned empty JSON content")

        try:
            raw_data = json.loads(content)
            return response_model.model_validate(raw_data)
        except JSONDecodeError as exc:
            raise LLMInvalidResponseError("DeepSeek returned invalid JSON") from exc
        except ValidationError as exc:
            raise LLMInvalidResponseError(
                "DeepSeek output did not match the expected schema"
            ) from exc
