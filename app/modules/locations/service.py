"""地点目录业务服务。"""

from typing import Protocol, cast
from uuid import UUID

from geoalchemy2.shape import to_shape
from pydantic import TypeAdapter
from shapely.geometry import Point
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.locations.models import Location
from app.modules.locations.normalization import normalize_location_text
from app.modules.locations.schemas import (
    LocationResolveRequest,
    LocationResolveResponse,
    LocationResponse,
    LocationSearchParams,
    LocationSearchResponse,
    LocationType,
)


class LocationRepositoryProtocol(Protocol):
    """LocationService 依赖的数据访问接口。

    Service 依赖协议而不是具体 Repository，
    方便测试时使用不访问真实数据库的 Stub。
    """

    async def get_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
    ) -> Location | None: ...

    async def find_exact(
        self,
        session: AsyncSession,
        normalized_query: str,
    ) -> list[Location]: ...

    async def search(
        self,
        session: AsyncSession,
        params: LocationSearchParams,
        normalized_query: str,
    ) -> tuple[list[Location], int]: ...


location_type_adapter = TypeAdapter(LocationType)


class LocationService:
    """处理地点搜索、标准化和解析状态判断。"""

    def __init__(
        self,
        repository: LocationRepositoryProtocol,
    ) -> None:
        self._repository = repository

    async def get_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
    ) -> LocationResponse | None:
        """查询标准地点详情。"""

        location = await self._repository.get_by_id(
            session,
            location_id,
        )

        if location is None:
            return None

        return self._to_response(location)

    async def search(
        self,
        session: AsyncSession,
        params: LocationSearchParams,
    ) -> LocationSearchResponse:
        """搜索标准名称或地点别名。"""

        normalized_query = normalize_location_text(params.query)

        # 输入可能只包含被标准化函数删除的分隔符。
        # 此时直接返回空结果，避免执行无意义的 contains("") 查询。
        if not normalized_query:
            return LocationSearchResponse(
                items=[],
                total=0,
                limit=params.limit,
                offset=params.offset,
            )

        locations, total = await self._repository.search(
            session,
            params,
            normalized_query,
        )

        return LocationSearchResponse(
            items=[
                self._to_response(location)
                for location in locations
            ],
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    async def resolve(
        self,
        session: AsyncSession,
        data: LocationResolveRequest,
    ) -> LocationResolveResponse:
        """将用户输入解析为零个、一个或多个标准地点。"""

        normalized_query = normalize_location_text(data.text)

        if not normalized_query:
            return LocationResolveResponse(
                query=data.text,
                normalized_query=normalized_query,
                status="not_found",
                matches=[],
            )

        locations = await self._repository.find_exact(
            session,
            normalized_query,
        )
        matches = [
            self._to_response(location)
            for location in locations
        ]

        if len(matches) == 1:
            status = "resolved"
        elif len(matches) >= 2:
            status = "ambiguous"
        else:
            status = "not_found"

        return LocationResolveResponse(
            query=data.text,
            normalized_query=normalized_query,
            status=status,
            matches=matches,
        )

    @staticmethod
    def _to_response(
        location: Location,
    ) -> LocationResponse:
        """将 ORM 地点转换为稳定的 API 响应。"""

        point = cast(
            Point,
            to_shape(location.location),
        )

        # 使用集合去重并排序，保证 API 输出顺序稳定，
        # 避免数据库返回顺序影响测试和前端展示。
        aliases = sorted(
            {
                alias.alias
                for alias in location.aliases
            }
        )

        return LocationResponse(
            id=location.id,
            canonical_name=location.canonical_name,
            location_type=location_type_adapter.validate_python(
                location.location_type,
            ),
            district=location.district,
            area=location.area,
            longitude=point.x,
            latitude=point.y,
            source=location.source,
            aliases=aliases,
            created_at=location.created_at,
            updated_at=location.updated_at,
        )