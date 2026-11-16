"""地点目录业务服务测试。"""

import asyncio
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.locations.models import Location, LocationAlias
from app.modules.locations.schemas import (
    LocationResolveRequest,
    LocationSearchParams,
)
from app.modules.locations.service import LocationService


class StubLocationRepository:
    """内存 Stub，用于隔离数据库测试地点业务规则。"""

    def __init__(
        self,
        exact_matches: list[Location] | None = None,
        search_matches: list[Location] | None = None,
    ) -> None:
        self.exact_matches = exact_matches or []
        self.search_matches = search_matches or []

        self.exact_queries: list[str] = []
        self.search_queries: list[str] = []

    async def get_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
    ) -> Location | None:
        """从预设数据中按 ID 查找地点。"""

        del session

        return next(
            (
                location
                for location in self.exact_matches
                if location.id == location_id
            ),
            None,
        )

    async def find_exact(
        self,
        session: AsyncSession,
        normalized_query: str,
    ) -> list[Location]:
        """记录精确查询并返回预设结果。"""

        del session

        self.exact_queries.append(normalized_query)
        return self.exact_matches

    async def search(
        self,
        session: AsyncSession,
        params: LocationSearchParams,
        normalized_query: str,
    ) -> tuple[list[Location], int]:
        """记录模糊搜索并返回预设结果。"""

        del session, params

        self.search_queries.append(normalized_query)

        return self.search_matches, len(self.search_matches)


def build_location(
    *,
    location_id: str,
    canonical_name: str,
    longitude: float,
    latitude: float,
    aliases: list[str],
) -> Location:
    """构造不需要写入数据库的 Location ORM 对象。"""

    now = datetime(2026, 11, 16, tzinfo=UTC)
    parsed_id = UUID(location_id)

    location = Location(
        id=parsed_id,
        canonical_name=canonical_name,
        normalized_name=canonical_name,
        location_type="office_area",
        district="浦东新区",
        area="张江",
        location=from_shape(
            Point(longitude, latitude),
            srid=4326,
        ),
        source="local_seed",
        source_id=f"test-{parsed_id}",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    location.aliases = [
        LocationAlias(
            location_id=parsed_id,
            alias=alias,
            normalized_alias=alias,
            created_at=now,
        )
        for alias in aliases
    ]

    return location


def fake_session() -> AsyncSession:
    """创建只用于满足 Service 方法签名的会话占位对象。"""

    return cast(AsyncSession, object())


def test_resolve_returns_single_standard_location() -> None:
    """唯一精确匹配应该返回 resolved。"""

    location = build_location(
        location_id="00000000-0000-4000-8000-000000000001",
        canonical_name="张江高科技园区",
        longitude=121.6000,
        latitude=31.2000,
        aliases=["张江科学城", "张江"],
    )
    repository = StubLocationRepository(
        exact_matches=[location],
    )
    service = LocationService(repository)

    response = asyncio.run(
        service.resolve(
            fake_session(),
            LocationResolveRequest(text="  张江-科学城  "),
        )
    )

    assert response.status == "resolved"
    assert response.normalized_query == "张江科学城"
    assert response.matches[0].canonical_name == "张江高科技园区"
    assert response.matches[0].longitude == 121.6000
    assert response.matches[0].latitude == 31.2000

    # Service 输出别名时应该去重并保持稳定排序。
    assert response.matches[0].aliases == [
        "张江",
        "张江科学城",
    ]
    assert repository.exact_queries == ["张江科学城"]


def test_resolve_returns_ambiguous_for_multiple_matches() -> None:
    """多个精确匹配必须要求澄清，不能擅自选择。"""

    first = build_location(
        location_id="00000000-0000-4000-8000-000000000001",
        canonical_name="张江高科技园区",
        longitude=121.6000,
        latitude=31.2000,
        aliases=["张江"],
    )
    second = build_location(
        location_id="00000000-0000-4000-8000-000000000002",
        canonical_name="张江高科地铁站",
        longitude=121.5876,
        latitude=31.2019,
        aliases=["张江"],
    )

    service = LocationService(
        StubLocationRepository(
            exact_matches=[first, second],
        )
    )

    response = asyncio.run(
        service.resolve(
            fake_session(),
            LocationResolveRequest(text="张江"),
        )
    )

    assert response.status == "ambiguous"
    assert len(response.matches) == 2


def test_resolve_returns_not_found_when_no_location_matches() -> None:
    """没有精确匹配时应该明确返回 not_found。"""

    service = LocationService(
        StubLocationRepository(),
    )

    response = asyncio.run(
        service.resolve(
            fake_session(),
            LocationResolveRequest(text="不存在的地点"),
        )
    )

    assert response.status == "not_found"
    assert response.matches == []


def test_separator_only_search_skips_repository() -> None:
    """标准化后为空的搜索不应该查询数据库。"""

    repository = StubLocationRepository()
    service = LocationService(repository)

    response = asyncio.run(
        service.search(
            fake_session(),
            LocationSearchParams(query=" · - ， "),
        )
    )

    assert response.items == []
    assert response.total == 0
    assert repository.search_queries == []