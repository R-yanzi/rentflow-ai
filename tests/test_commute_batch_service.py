"""批量通勤编排 Service 测试。"""

from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commutes.batch_service import CommuteBatchService
from app.modules.commutes.exceptions import (
    CommuteDestinationNotFoundError,
    CommuteListingsNotFoundError,
)
from app.modules.commutes.schemas import (
    CommuteBatchRequest,
    CommuteCalculation,
)
from app.modules.listings.models import Listing
from app.modules.locations.models import Location
from app.providers.commute.base import (
    CommuteMode,
    CommuteRequest,
    CommuteResult,
)

FIRST_LISTING_ID = UUID(
    "00000000-0000-4000-8000-000000000001",
)
SECOND_LISTING_ID = UUID(
    "00000000-0000-4000-8000-000000000002",
)
DESTINATION_ID = UUID(
    "00000000-0000-4000-8000-000000000099",
)
CALCULATED_AT = datetime(2026, 11, 17, 8, 0, tzinfo=UTC)


def create_listing(
    listing_id: UUID,
    *,
    longitude: float,
    latitude: float,
) -> Listing:
    """构造带 PostGIS 坐标的测试房源。"""

    return Listing(
        id=listing_id,
        location=from_shape(
            Point(longitude, latitude),
            srid=4326,
        ),
    )


def create_destination() -> Location:
    """构造带 PostGIS 坐标的标准目的地点。"""

    return Location(
        id=DESTINATION_ID,
        location=from_shape(
            Point(121.593, 31.207),
            srid=4326,
        ),
    )


class StubListingRepository:
    """返回预设房源，并记录批量查询参数。"""

    def __init__(
        self,
        listings: list[Listing],
    ) -> None:
        self.listings = listings
        self.calls = 0
        self.last_listing_ids: list[UUID] | None = None

    async def get_by_ids(
        self,
        session: AsyncSession,
        listing_ids: list[UUID],
    ) -> list[Listing]:
        """返回预设房源。"""

        del session
        self.calls += 1
        self.last_listing_ids = list(listing_ids)
        return self.listings


class StubLocationRepository:
    """返回预设目的地点。"""

    def __init__(
        self,
        location: Location | None,
    ) -> None:
        self.location = location
        self.calls = 0

    async def get_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
    ) -> Location | None:
        """返回预设地点。"""

        del session, location_id
        self.calls += 1
        return self.location


class StubCommuteCalculator:
    """记录批量编排生成的单条通勤请求。"""

    def __init__(self) -> None:
        self.calls: list[
            tuple[
                UUID,
                UUID,
                CommuteRequest,
            ]
        ] = []

    async def calculate(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        destination_location_id: UUID,
        request: CommuteRequest,
    ) -> CommuteCalculation:
        """记录请求并返回固定计算结果。"""

        del session

        self.calls.append(
            (
                listing_id,
                destination_location_id,
                request,
            )
        )

        return CommuteCalculation(
            result=CommuteResult(
                mode=request.mode,
                distance_meters=8_500,
                duration_minutes=32,
                provider="local_estimate_v1",
                is_estimated=True,
                calculated_at=CALCULATED_AT,
            ),
            cache_hit=False,
            expires_at=CALCULATED_AT + timedelta(hours=24),
        )


def create_session_mock() -> AsyncSession:
    """创建满足严格类型检查的 Session Mock。"""

    return cast(
        AsyncSession,
        AsyncMock(spec=AsyncSession),
    )


@pytest.mark.anyio
async def test_batch_restores_request_order_and_coordinates() -> None:
    """数据库乱序返回时，响应和计算调用仍应保持请求顺序。"""

    first_listing = create_listing(
        FIRST_LISTING_ID,
        longitude=121.610,
        latitude=31.210,
    )
    second_listing = create_listing(
        SECOND_LISTING_ID,
        longitude=121.620,
        latitude=31.220,
    )

    # 故意按照 first、second 返回，
    # 但请求顺序是 second、first。
    listing_repository = StubListingRepository(
        [
            first_listing,
            second_listing,
        ]
    )
    location_repository = StubLocationRepository(
        create_destination(),
    )
    calculator = StubCommuteCalculator()
    service = CommuteBatchService(
        listing_repository,
        location_repository,
        calculator,
    )

    request = CommuteBatchRequest(
        listing_ids=[
            SECOND_LISTING_ID,
            FIRST_LISTING_ID,
        ],
        destination_location_id=DESTINATION_ID,
        mode=CommuteMode.TRANSIT,
    )

    response = await service.calculate(
        create_session_mock(),
        request,
    )

    assert [item.listing_id for item in response.items] == [
        SECOND_LISTING_ID,
        FIRST_LISTING_ID,
    ]

    assert [call[0] for call in calculator.calls] == [
        SECOND_LISTING_ID,
        FIRST_LISTING_ID,
    ]

    first_call_request = calculator.calls[0][2]
    second_call_request = calculator.calls[1][2]

    assert first_call_request.origin.longitude == pytest.approx(121.620)
    assert first_call_request.origin.latitude == pytest.approx(31.220)
    assert second_call_request.origin.longitude == pytest.approx(121.610)
    assert second_call_request.origin.latitude == pytest.approx(31.210)

    assert first_call_request.destination.longitude == pytest.approx(121.593)
    assert first_call_request.destination.latitude == pytest.approx(31.207)

    assert listing_repository.last_listing_ids == [
        SECOND_LISTING_ID,
        FIRST_LISTING_ID,
    ]


@pytest.mark.anyio
async def test_missing_destination_stops_before_listing_query() -> None:
    """目的地不存在时不应继续读取房源或调用计算器。"""

    listing_repository = StubListingRepository([])
    location_repository = StubLocationRepository(None)
    calculator = StubCommuteCalculator()
    service = CommuteBatchService(
        listing_repository,
        location_repository,
        calculator,
    )

    request = CommuteBatchRequest(
        listing_ids=[FIRST_LISTING_ID],
        destination_location_id=DESTINATION_ID,
        mode=CommuteMode.TRANSIT,
    )

    with pytest.raises(
        CommuteDestinationNotFoundError,
    ) as exception_info:
        await service.calculate(
            create_session_mock(),
            request,
        )

    assert exception_info.value.destination_location_id == DESTINATION_ID
    assert listing_repository.calls == 0
    assert calculator.calls == []


@pytest.mark.anyio
async def test_missing_listings_report_ids_without_partial_calculation() -> None:
    """房源缺失时应整体失败，并按请求顺序报告缺失 ID。"""

    first_listing = create_listing(
        FIRST_LISTING_ID,
        longitude=121.610,
        latitude=31.210,
    )
    listing_repository = StubListingRepository(
        [first_listing],
    )
    location_repository = StubLocationRepository(
        create_destination(),
    )
    calculator = StubCommuteCalculator()
    service = CommuteBatchService(
        listing_repository,
        location_repository,
        calculator,
    )

    request = CommuteBatchRequest(
        listing_ids=[
            SECOND_LISTING_ID,
            FIRST_LISTING_ID,
        ],
        destination_location_id=DESTINATION_ID,
        mode=CommuteMode.TRANSIT,
    )

    with pytest.raises(
        CommuteListingsNotFoundError,
    ) as exception_info:
        await service.calculate(
            create_session_mock(),
            request,
        )

    assert exception_info.value.missing_listing_ids == [
        SECOND_LISTING_ID,
    ]
    assert calculator.calls == []
