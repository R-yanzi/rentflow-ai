"""批量通勤 HTTP API 测试。"""

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.modules.commutes.batch_service import CommuteBatchService
from app.modules.commutes.dependencies import get_commute_batch_service
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
from app.providers.commute.base import (
    CommuteMode,
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


def create_calculation(
    *,
    cache_hit: bool,
) -> CommuteCalculation:
    """构造固定通勤结果。"""

    return CommuteCalculation(
        result=CommuteResult(
            mode=CommuteMode.TRANSIT,
            distance_meters=8_500,
            duration_minutes=32,
            provider="local_estimate_v1",
            is_estimated=True,
            calculated_at=CALCULATED_AT,
        ),
        cache_hit=cache_hit,
        expires_at=CALCULATED_AT + timedelta(hours=24),
    )


def create_success_response() -> CommuteBatchResponse:
    """构造保持房源顺序的成功响应。"""

    return CommuteBatchResponse(
        destination_location_id=DESTINATION_ID,
        mode=CommuteMode.TRANSIT,
        items=[
            ListingCommuteCalculation(
                listing_id=SECOND_LISTING_ID,
                calculation=create_calculation(
                    cache_hit=False,
                ),
            ),
            ListingCommuteCalculation(
                listing_id=FIRST_LISTING_ID,
                calculation=create_calculation(
                    cache_hit=True,
                ),
            ),
        ],
    )


class StubCommuteBatchService:
    """返回固定响应或抛出指定领域异常。"""

    def __init__(
        self,
        *,
        response: CommuteBatchResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls = 0
        self.last_request: CommuteBatchRequest | None = None

    async def calculate(
        self,
        session: AsyncSession,
        request: CommuteBatchRequest,
    ) -> CommuteBatchResponse:
        """记录请求并返回预设结果。"""

        del session
        self.calls += 1
        self.last_request = request

        if self.error is not None:
            raise self.error

        if self.response is None:
            raise AssertionError("Stub response was not configured")

        return self.response


def create_test_client(
    service: StubCommuteBatchService,
) -> tuple[TestClient, StubCommuteBatchService]:
    """创建覆盖真实通勤依赖的测试客户端。"""

    application = create_app()

    def override_service() -> CommuteBatchService:
        return cast(
            CommuteBatchService,
            service,
        )

    application.dependency_overrides[get_commute_batch_service] = override_service

    return TestClient(application), service


def valid_request_body() -> dict[str, object]:
    """构造合法批量请求 JSON。"""

    return {
        "listing_ids": [
            str(SECOND_LISTING_ID),
            str(FIRST_LISTING_ID),
        ],
        "destination_location_id": str(
            DESTINATION_ID,
        ),
        "mode": "transit",
    }


def test_batch_commute_api_returns_structured_result() -> None:
    """成功响应应保留顺序、来源和缓存状态。"""

    client, service = create_test_client(
        StubCommuteBatchService(
            response=create_success_response(),
        )
    )

    with client:
        response = client.post(
            "/api/v1/commutes/calculate",
            json=valid_request_body(),
        )

    body = response.json()

    assert response.status_code == 200
    assert body["destination_location_id"] == str(
        DESTINATION_ID,
    )
    assert body["mode"] == "transit"
    assert [item["listing_id"] for item in body["items"]] == [
        str(SECOND_LISTING_ID),
        str(FIRST_LISTING_ID),
    ]
    assert body["items"][0]["calculation"]["cache_hit"] is False
    assert body["items"][1]["calculation"]["cache_hit"] is True
    assert body["items"][0]["calculation"]["result"]["provider"] == "local_estimate_v1"

    assert service.calls == 1
    assert service.last_request is not None
    assert service.last_request.mode is CommuteMode.TRANSIT


def test_missing_destination_has_standard_error_response() -> None:
    """未知目的地应返回带 Request ID 的标准 404。"""

    client, _ = create_test_client(
        StubCommuteBatchService(
            error=CommuteDestinationNotFoundError(
                DESTINATION_ID,
            )
        )
    )

    with client:
        response = client.post(
            "/api/v1/commutes/calculate",
            json=valid_request_body(),
        )

    body = response.json()

    assert response.status_code == 404
    assert body["code"] == "COMMUTE_DESTINATION_NOT_FOUND"
    assert body["details"] == {
        "destination_location_id": str(
            DESTINATION_ID,
        )
    }
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_missing_listings_returns_machine_readable_ids() -> None:
    """缺失房源应通过 details 返回 UUID 列表。"""

    client, _ = create_test_client(
        StubCommuteBatchService(
            error=CommuteListingsNotFoundError(
                [
                    SECOND_LISTING_ID,
                    FIRST_LISTING_ID,
                ]
            )
        )
    )

    with client:
        response = client.post(
            "/api/v1/commutes/calculate",
            json=valid_request_body(),
        )

    body = response.json()

    assert response.status_code == 404
    assert body["code"] == "COMMUTE_LISTINGS_NOT_FOUND"
    assert body["details"]["missing_listing_ids"] == [
        str(SECOND_LISTING_ID),
        str(FIRST_LISTING_ID),
    ]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_invalid_batch_request_returns_422_without_calling_service() -> None:
    """重复房源 ID 应在进入业务层前被拒绝。"""

    service = StubCommuteBatchService(
        response=create_success_response(),
    )
    client, service = create_test_client(service)

    request_body = valid_request_body()
    request_body["listing_ids"] = [
        str(FIRST_LISTING_ID),
        str(FIRST_LISTING_ID),
    ]

    with client:
        response = client.post(
            "/api/v1/commutes/calculate",
            json=request_body,
        )

    assert response.status_code == 422
    assert service.calls == 0
