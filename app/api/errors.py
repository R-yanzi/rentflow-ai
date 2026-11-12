"""统一 API 错误响应模型。"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """返回给客户端的标准错误结构。"""

    code: str
    message: str
    request_id: str
