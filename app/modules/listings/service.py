"""房源业务服务。"""

from typing import cast
from uuid import UUID

from geoalchemy2.shape import to_shape
from pydantic import TypeAdapter
from shapely.geometry import Point
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.models import Listing
from app.modules.listings.repository import ListingRepository
from app.modules.listings.schemas import (
    ListingCreate,
    ListingListResponse,
    ListingResponse,
    ListingSearchParams,
    ListingStatus,
)

# ORM 返回普通 str，但 API 只允许四种状态。
# TypeAdapter 会执行运行时验证，并将类型收窄为 ListingStatus。
listing_status_adapter = TypeAdapter(ListingStatus)


class ListingService:
    """处理房源业务与事务边界。"""

    def __init__(self, repository: ListingRepository) -> None:
        self._repository = repository

    async def create(
        self,
        session: AsyncSession,
        data: ListingCreate,
    ) -> ListingResponse:
        """创建房源并提交事务。"""
        try:
            listing = await self._repository.create(session, data)
            await session.commit()
        except Exception:
            # 发生异常时显式回滚，确保会话可以继续安全使用。
            await session.rollback()
            raise

        return self._to_response(listing)

    async def get_by_id(
        self,
        session: AsyncSession,
        listing_id: UUID,
    ) -> ListingResponse | None:
        """查询房源详情。"""
        listing = await self._repository.get_by_id(session, listing_id)

        if listing is None:
            return None

        return self._to_response(listing)

    async def search(
        self,
        session: AsyncSession,
        params: ListingSearchParams,
    ) -> ListingListResponse:
        """根据确定性条件筛选房源。"""

        listing_rows, total = await self._repository.search(session, params)

        return ListingListResponse(
            items=[self._to_response(listing, distance_m) for listing, distance_m in listing_rows],
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    @staticmethod
    def _to_response(
        listing: Listing,
        distance_m: float | None = None,
    ) -> ListingResponse:
        """将 ORM 对象转换成稳定的 API 响应模型。"""

        point = cast(Point, to_shape(listing.location))

        return ListingResponse(
            id=listing.id,
            title=listing.title,
            district=listing.district,
            monthly_rent=listing.monthly_rent,
            bedrooms=listing.bedrooms,
            area_sqm=listing.area_sqm,
            floor=listing.floor,
            orientation=listing.orientation,
            pets_allowed=listing.pets_allowed,
            near_main_road=listing.near_main_road,
            available_date=listing.available_date,
            subway_distance_m=listing.subway_distance_m,
            description=listing.description,
            longitude=point.x,
            latitude=point.y,
            status=listing_status_adapter.validate_python(listing.status),
            created_at=listing.created_at,
            updated_at=listing.updated_at,
            distance_m=round(distance_m, 2) if distance_m is not None else None,
            area=listing.area,
        )
