"""地点目录 HTTP API 测试。"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.modules.locations.dependencies import get_location_service
from app.modules.locations.schemas import (
    LocationResolveRequest,
    LocationResolveResponse,
    LocationResponse,
    LocationSearchParams,
    LocationSearchResponse,
)

LOCATION_ID = UUID(
    "00000000-0000-4000-8000-000000000001",
)


def build_location_response() -> LocationResponse:
    """构造 API 测试使用的标准地点。"""

    now = datetime(2026, 11, 16, tzinfo=UTC)

    return LocationResponse(
        id=LOCATION_ID,
        canonical_name="张江高科技园区",
        location_type="office_area",
        district="浦东新区",
        area="张江",
        longitude=121.6000,
        latitude=31.2000,
        source="local_seed",
        aliases=["张江", "张江科学城"],
        created_at=now,
        updated_at=now,
    )


class StubLocationService:
    """不访问数据库的地点服务。"""

    def __init__(self) -> None:
        self.last_search_params: LocationSearchParams | None = None
        self.last_resolve_request: LocationResolveRequest | None = None

    async def search(
        self,
        session: AsyncSession,
        params: LocationSearchParams,
    ) -> LocationSearchResponse:
        """记录查询参数并返回固定搜索结果。"""

        del session
        self.last_search_params = params

        return LocationSearchResponse(
            items=[build_location_response()],
            total=1,
            limit=params.limit,
            offset=params.offset,
        )

    async def resolve(
        self,
        session: AsyncSession,
        data: LocationResolveRequest,
    ) -> LocationResolveResponse:
        """记录解析请求并返回唯一匹配。"""

        del session
        self.last_resolve_request = data

        return LocationResolveResponse(
            query=data.text,
            normalized_query="张江",
            status="resolved",
            matches=[build_location_response()],
        )

    async def get_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
    ) -> LocationResponse | None:
        """只有测试地点 UUID 可以查询成功。"""

        del session

        if location_id == LOCATION_ID:
            return build_location_response()

        return None


def create_test_client(
    service: StubLocationService,
) -> TestClient:
    """创建覆盖真实地点服务的测试客户端。"""

    application = create_app()

    def provide_stub_service() -> StubLocationService:
        return service

    application.dependency_overrides[
        get_location_service
    ] = provide_stub_service

    return TestClient(application)


def test_search_locations_uses_fixed_search_route() -> None:
    """搜索路径不能被动态 UUID 路由错误拦截。"""

    service = StubLocationService()

    with create_test_client(service) as client:
        response = client.get(
            "/api/v1/locations/search",
            params={
                "query": "张江",
                "location_type": "office_area",
                "limit": 10,
                "offset": 0,
            },
        )

    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 1
    assert body["items"][0]["canonical_name"] == "张江高科技园区"

    assert service.last_search_params is not None
    assert service.last_search_params.query == "张江"
    assert service.last_search_params.location_type == "office_area"
    assert service.last_search_params.limit == 10


def test_resolve_location_returns_explicit_status() -> None:
    """解析接口应该返回标准地点和明确状态。"""

    service = StubLocationService()

    with create_test_client(service) as client:
        response = client.post(
            "/api/v1/locations/resolve",
            json={
                "text": "张江",
            },
        )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "resolved"
    assert len(body["matches"]) == 1
    assert body["matches"][0]["id"] == str(LOCATION_ID)

    assert service.last_resolve_request is not None
    assert service.last_resolve_request.text == "张江"


def test_get_location_returns_404_when_not_found() -> None:
    """不存在的地点应该返回 HTTP 404。"""

    service = StubLocationService()
    missing_id = "00000000-0000-4000-8000-000000000999"

    with create_test_client(service) as client:
        response = client.get(
            f"/api/v1/locations/{missing_id}",
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Location not found",
    }


def test_search_locations_rejects_blank_query() -> None:
    """空白搜索词应该在进入 Service 前返回 422。"""

    service = StubLocationService()

    with create_test_client(service) as client:
        response = client.get(
            "/api/v1/locations/search",
            params={
                "query": "   ",
            },
        )

    assert response.status_code == 422
    assert service.last_search_params is None