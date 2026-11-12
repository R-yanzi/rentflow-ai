"""LLM 全局异常处理测试。"""

from fastapi.testclient import TestClient

from app.main import create_app
from app.providers.llm.base import LLMProvider
from app.providers.llm.dependencies import get_llm_provider
from app.providers.llm.exceptions import LLMConfigurationError


def unavailable_provider() -> LLMProvider:
    """模拟模型没有配置。"""
    raise LLMConfigurationError("Missing API key")


def test_llm_configuration_error_has_standard_response() -> None:
    """依赖解析错误也应转换成统一响应。"""

    application = create_app()
    application.dependency_overrides[get_llm_provider] = unavailable_provider

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/search/requirements",
            json={"text": "预算5000，想在张江租房"},
        )

    body = response.json()

    assert response.status_code == 503
    assert body["code"] == "LLM_NOT_CONFIGURED"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
