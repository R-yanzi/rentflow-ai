"""系统健康检查接口。"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session

router = APIRouter(prefix="/health", tags=["System"])

# 使用 Annotated 声明配置依赖。
# FastAPI 会在处理请求时调用 get_settings() 获取配置。
SettingsDependency = Annotated[Settings, Depends(get_settings)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


class HealthResponse(BaseModel):
    """健康检查接口的响应结构。"""

    status: Literal["ok"]
    service: str
    version: str


class ReadinessResponse(BaseModel):
    """服务就绪检查响应。"""

    status: Literal["ready"]
    database: Literal["available"]


@router.get(
    "",
    response_model=HealthResponse,
    summary="检查服务是否正常运行",
)
async def health_check(settings: SettingsDependency) -> HealthResponse:
    """返回当前 API 服务的基础运行状态。"""
    return HealthResponse(
        status="ok",
        service=settings.name,
        version=settings.version,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="检查服务依赖是否就绪",
)
async def readiness_check(session: DatabaseSession) -> ReadinessResponse:
    """执行轻量 SQL，验证数据库连接是否可用。"""

    # 使用 text() 明确声明原生 SQL，SQLAlchemy 2.x 不接受裸字符串 SQL。
    await session.execute(text("SELECT 1"))

    return ReadinessResponse(
        status="ready",
        database="available",
    )
