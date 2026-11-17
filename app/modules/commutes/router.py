"""通勤计算 HTTP API。"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.commutes.batch_service import CommuteBatchService
from app.modules.commutes.dependencies import get_commute_batch_service
from app.modules.commutes.schemas import (
    CommuteBatchRequest,
    CommuteBatchResponse,
)

router = APIRouter(
    prefix="/commutes",
    tags=["Commutes"],
)

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]

CommuteBatchServiceDependency = Annotated[
    CommuteBatchService,
    Depends(get_commute_batch_service),
]


@router.post(
    "/calculate",
    response_model=CommuteBatchResponse,
    summary="批量计算房源到标准地点的通勤",
)
async def calculate_commutes(
    request: CommuteBatchRequest,
    session: DatabaseSession,
    service: CommuteBatchServiceDependency,
) -> CommuteBatchResponse:
    """根据房源 ID、标准地点和交通方式计算通勤。"""

    return await service.calculate(
        session,
        request,
    )
