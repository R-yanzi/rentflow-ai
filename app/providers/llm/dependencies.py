"""LLM Provider 依赖装配。"""

from functools import lru_cache

from app.core.config import get_settings
from app.providers.llm.base import LLMProvider
from app.providers.llm.deepseek import DeepSeekProvider
from app.providers.llm.exceptions import LLMConfigurationError


@lru_cache
def get_llm_provider() -> LLMProvider:
    """根据应用配置创建并缓存 DeepSeek Provider。"""

    settings = get_settings()

    if settings.deepseek_api_key is None:
        raise LLMConfigurationError("DeepSeek API key is not configured")

    api_key = settings.deepseek_api_key.get_secret_value()

    if not api_key:
        raise LLMConfigurationError("DeepSeek API key is empty")

    return DeepSeekProvider(
        api_key=api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout_seconds=settings.deepseek_timeout_seconds,
        max_tokens=settings.deepseek_max_tokens,
    )
