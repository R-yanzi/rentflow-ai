"""应用全局异常处理器。"""

from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.errors import ErrorResponse
from app.providers.llm.exceptions import (
    LLMConfigurationError,
    LLMEmptyResponseError,
    LLMError,
    LLMInvalidResponseError,
    LLMTimeoutError,
    LLMUpstreamError,
)


def get_request_id(request: Request) -> str:
    """读取中间件创建的 Request ID。"""
    return str(
        getattr(
            request.state,
            "request_id",
            uuid4(),
        )
    )


async def handle_llm_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """将内部 LLM 异常转换成稳定的 HTTP 响应。"""

    if isinstance(exc, LLMConfigurationError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        code = "LLM_NOT_CONFIGURED"
        message = "The language model service is not configured"
    elif isinstance(exc, LLMTimeoutError):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        code = "LLM_TIMEOUT"
        message = "The language model request timed out"
    elif isinstance(exc, LLMEmptyResponseError):
        status_code = status.HTTP_502_BAD_GATEWAY
        code = "LLM_EMPTY_RESPONSE"
        message = "The language model returned an empty response"
    elif isinstance(exc, LLMInvalidResponseError):
        status_code = status.HTTP_502_BAD_GATEWAY
        code = "LLM_INVALID_RESPONSE"
        message = "The language model returned an invalid response"
    elif isinstance(exc, LLMUpstreamError):
        status_code = status.HTTP_502_BAD_GATEWAY
        code = "LLM_UPSTREAM_ERROR"
        message = "The language model service is unavailable"
    else:
        status_code = status.HTTP_502_BAD_GATEWAY
        code = "LLM_PROVIDER_ERROR"
        message = "The language model request failed"

    body = ErrorResponse(
        code=code,
        message=message,
        request_id=get_request_id(request),
    )

    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
    )


def register_exception_handlers(application: FastAPI) -> None:
    """注册应用级异常映射。"""

    application.add_exception_handler(
        LLMError,
        handle_llm_error,
    )
