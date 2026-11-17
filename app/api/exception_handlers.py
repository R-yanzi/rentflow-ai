"""应用全局异常处理器。"""

from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.errors import ErrorResponse
from app.modules.commutes.exceptions import (
    CommuteBatchError,
    CommuteDestinationNotFoundError,
    CommuteListingsNotFoundError,
)
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
        content=body.model_dump(
            mode="json",
            exclude_none=True,
        ),
    )


async def handle_commute_batch_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """将通勤领域异常转换为稳定的 HTTP 404 响应。"""

    if isinstance(
        exc,
        CommuteDestinationNotFoundError,
    ):
        code = "COMMUTE_DESTINATION_NOT_FOUND"
        message = "The destination location was not found"
        details: dict[str, str | list[str]] = {
            "destination_location_id": str(
                exc.destination_location_id,
            )
        }
    elif isinstance(
        exc,
        CommuteListingsNotFoundError,
    ):
        code = "COMMUTE_LISTINGS_NOT_FOUND"
        message = "One or more listings were not found"
        details = {
            "missing_listing_ids": [str(listing_id) for listing_id in exc.missing_listing_ids]
        }
    else:
        # 该分支理论上不会出现，但保留稳定的基类兜底。
        code = "COMMUTE_BATCH_ERROR"
        message = "The commute batch request failed"
        details = {}

    body = ErrorResponse(
        code=code,
        message=message,
        request_id=get_request_id(request),
        details=details,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=body.model_dump(
            mode="json",
            exclude_none=True,
        ),
    )


def register_exception_handlers(application: FastAPI) -> None:
    """注册应用级异常映射。"""

    application.add_exception_handler(
        LLMError,
        handle_llm_error,
    )

    application.add_exception_handler(
        CommuteBatchError,
        handle_commute_batch_error,
    )
