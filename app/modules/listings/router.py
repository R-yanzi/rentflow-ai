"""房源 HTTP API。"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.listings.dependencies import get_listing_service
from app.modules.listings.schemas import (
    ListingCreate,
    ListingListResponse,
    ListingResponse,
    ListingSearchParams,
)
from app.modules.listings.service import ListingService

router = APIRouter(prefix="/listings", tags=["Listings"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
ListingServiceDependency = Annotated[
    ListingService,
    Depends(get_listing_service),
]


@router.post(
    "",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建房源",
)
async def create_listing(
    data: ListingCreate,
    session: DatabaseSession,
    service: ListingServiceDependency,
) -> ListingResponse:
    """创建一条新的租赁房源。"""
    return await service.create(session, data)


@router.get(
    "",
    response_model=ListingListResponse,
    summary="筛选房源列表",
)
async def search_listings(
    session: DatabaseSession,
    params: Annotated[ListingSearchParams, Query()],
    service: ListingServiceDependency,
) -> ListingListResponse:
    """根据结构化硬条件筛选可租房源。

    FastAPI 直接将查询参数解析为 ListingSearchParams。
    字段约束或跨字段校验失败时，会自动返回 HTTP 422。
    """
    return await service.search(session, params)


@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="查询房源详情",
)
async def get_listing(
    listing_id: UUID,
    session: DatabaseSession,
    service: ListingServiceDependency,
) -> ListingResponse:
    """根据 UUID 查询单个房源。"""
    listing = await service.get_by_id(session, listing_id)

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    return listing
