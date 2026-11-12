"""LLM Provider 异常体系。"""


class LLMError(RuntimeError):
    """所有 LLM 应用异常的基类。"""


class LLMConfigurationError(LLMError):
    """模型配置缺失或无效。"""


class LLMProviderError(LLMError):
    """模型 Provider 请求或响应异常。"""


class LLMTimeoutError(LLMProviderError):
    """模型请求超时。"""


class LLMUpstreamError(LLMProviderError):
    """模型网络连接或上游 API 异常。"""


class LLMEmptyResponseError(LLMProviderError):
    """模型返回空白内容。"""


class LLMInvalidResponseError(LLMProviderError):
    """模型返回内容不符合 JSON 或业务 Schema。"""
