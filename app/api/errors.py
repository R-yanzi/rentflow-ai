"""统一 API 错误响应模型。"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """返回给客户端的标准错误结构。"""

    code: str
    message: str
    request_id: str

    # details 用于返回可机器读取的业务上下文，
    # 例如缺失房源 ID；没有额外信息时不输出该字段。
    details: dict[str, str | list[str]] | None = None
