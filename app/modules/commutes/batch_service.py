"""房源到标准地点的批量通勤编排服务。"""

from typing import Protocol, cast
from uuid import UUID

from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commutes.exceptions import (
    CommuteDestinationNotFoundError,
    CommuteListingsNotFoundError,
)
from app.modules.commutes.schemas import (
    CommuteBatchRequest,
    CommuteBatchResponse,
    CommuteCalculation,
    ListingCommuteCalculation,
)
from app.modules.listings.models import Listing
from app.modules.locations.models import Location
from app.providers.commute.base import (
    CommuteRequest,
    Coordinate,
)


class BatchListingRepositoryProtocol(Protocol):
    """批量通勤编排需要的房源查询接口。"""

    async def get_by_ids(
        self,
        session: AsyncSession,
        listing_ids: list[UUID],
    ) -> list[Listing]: ...


class BatchLocationRepositoryProtocol(Protocol):
    """批量通勤编排需要的地点查询接口。"""

    async def get_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
    ) -> Location | None: ...


class CommuteCalculatorProtocol(Protocol):
    """批量编排依赖的单条通勤计算接口。"""

    async def calculate(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        destination_location_id: UUID,
        request: CommuteRequest,
    ) -> CommuteCalculation: ...


class CommuteBatchService:
    """批量读取业务实体并复用单条缓存通勤计算。"""

    def __init__(
        self,
        listing_repository: BatchListingRepositoryProtocol,
        location_repository: BatchLocationRepositoryProtocol,
        calculator: CommuteCalculatorProtocol,
    ) -> None:
        self._listing_repository = listing_repository
        self._location_repository = location_repository
        self._calculator = calculator

    async def calculate(
        self,
        session: AsyncSession,
        request: CommuteBatchRequest,
    ) -> CommuteBatchResponse:
        """按请求房源顺序返回批量通勤结果。"""

        destination = await self._location_repository.get_by_id(
            session,
            request.destination_location_id,
        )

        if destination is None:
            # 地点不存在时不能猜测坐标或继续计算。
            raise CommuteDestinationNotFoundError(
                request.destination_location_id,
            )

        listings = await self._listing_repository.get_by_ids(
            session,
            request.listing_ids,
        )

        listing_by_id = {listing.id: listing for listing in listings}

        # 按请求顺序收集缺失 ID，使错误信息稳定且易于前端对应。
        missing_listing_ids = [
            listing_id for listing_id in request.listing_ids if listing_id not in listing_by_id
        ]

        if missing_listing_ids:
            # 批量接口采用全有或全无语义。
            # 有房源缺失时不返回不完整的部分结果。
            raise CommuteListingsNotFoundError(
                missing_listing_ids,
            )

        destination_coordinate = self._to_coordinate(
            destination.location,
        )

        items: list[ListingCommuteCalculation] = []

        # 这里严格按照请求 ID 顺序读取字典，
        # 不依赖 SQL IN 查询的返回顺序。
        for listing_id in request.listing_ids:
            listing = listing_by_id[listing_id]

            commute_request = CommuteRequest(
                origin=self._to_coordinate(listing.location),
                destination=destination_coordinate,
                mode=request.mode,
            )

            calculation = await self._calculator.calculate(
                session,
                listing_id=listing.id,
                destination_location_id=destination.id,
                request=commute_request,
            )

            items.append(
                ListingCommuteCalculation(
                    listing_id=listing.id,
                    calculation=calculation,
                )
            )

        return CommuteBatchResponse(
            destination_location_id=destination.id,
            mode=request.mode,
            items=items,
        )

    @staticmethod
    def _to_coordinate(
        value: WKBElement,
    ) -> Coordinate:
        """把 PostGIS WKB Point 转换为通勤 Provider 坐标。"""

        point = cast(
            Point,
            to_shape(value),
        )

        return Coordinate(
            longitude=point.x,
            latitude=point.y,
        )
