"""地点目录 HTTP API。"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.locations.dependencies import get_location_service
from app.modules.locations.schemas import (
    LocationResolveRequest,
    LocationResolveResponse,
    LocationResponse,
    LocationSearchParams,
    LocationSearchResponse,
)
from app.modules.locations.service import LocationService

router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
)

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]

LocationServiceDependency = Annotated[
    LocationService,
    Depends(get_location_service),
]


@router.get(
    "/search",
    response_model=LocationSearchResponse,
    summary="搜索上海地点目录",
)
async def search_locations(
    session: DatabaseSession,
    params: Annotated[LocationSearchParams, Query()],
    service: LocationServiceDependency,
) -> LocationSearchResponse:
    """根据标准名称或别名分页搜索地点。"""

    return await service.search(
        session,
        params,
    )


@router.post(
    "/resolve",
    response_model=LocationResolveResponse,
    summary="解析标准地点",
)
async def resolve_location(
    request: LocationResolveRequest,
    session: DatabaseSession,
    service: LocationServiceDependency,
) -> LocationResolveResponse:
    """将用户输入解析为唯一地点、歧义候选或未找到。"""

    return await service.resolve(
        session,
        request,
    )


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    summary="查询地点详情",
)
async def get_location(
    location_id: UUID,
    session: DatabaseSession,
    service: LocationServiceDependency,
) -> LocationResponse:
    """根据 UUID 查询标准地点。"""

    location = await service.get_by_id(
        session,
        location_id,
    )

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    return location