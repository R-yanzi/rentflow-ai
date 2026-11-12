"""HTTP Request ID 中间件。"""

from uuid import uuid4

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """为每个 HTTP 请求生成唯一追踪 ID。"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = str(uuid4())

        # 异常处理器和后续日志可以从 request.state 中读取。
        request.state.request_id = request_id

        response = await call_next(request)

        # 前端反馈问题时可以附带此 ID。
        response.headers["X-Request-ID"] = request_id

        return response
