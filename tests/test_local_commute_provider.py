"""本地通勤估算 Provider 测试。"""

import pytest

from app.providers.commute.base import (
    CommuteMode,
    CommuteRequest,
    Coordinate,
)
from app.providers.commute.local import (
    LocalEstimateCommuteProvider,
    haversine_distance,
)


def create_request(mode: CommuteMode) -> CommuteRequest:
    """构造从金桥附近到张江的固定测试请求。"""

    return CommuteRequest(
        origin=Coordinate(
            longitude=121.602,
            latitude=31.258,
        ),
        destination=Coordinate(
            longitude=121.593,
            latitude=31.207,
        ),
        mode=mode,
    )


def test_haversine_distance_is_symmetric() -> None:
    """交换起点和终点不应改变球面直线距离。"""

    request = create_request(CommuteMode.TRANSIT)

    forward = haversine_distance(
        request.origin,
        request.destination,
    )
    backward = haversine_distance(
        request.destination,
        request.origin,
    )

    assert forward == pytest.approx(backward)
    assert forward > 0


@pytest.mark.anyio
async def test_local_provider_marks_result_as_estimated() -> None:
    """本地结果必须显式说明它只是估算值。"""

    provider = LocalEstimateCommuteProvider()

    result = await provider.calculate(
        create_request(CommuteMode.TRANSIT),
    )

    assert result.mode is CommuteMode.TRANSIT
    assert result.distance_meters > 0
    assert result.duration_minutes > 0
    assert result.provider == "local_estimate_v1"
    assert result.is_estimated is True
    assert result.calculated_at.tzinfo is not None


@pytest.mark.anyio
async def test_batch_preserves_request_order() -> None:
    """批量计算结果必须与请求顺序一一对应。"""

    provider = LocalEstimateCommuteProvider()
    requests = [
        create_request(CommuteMode.WALKING),
        create_request(CommuteMode.BICYCLING),
        create_request(CommuteMode.TRANSIT),
        create_request(CommuteMode.DRIVING),
    ]

    results = await provider.calculate_batch(requests)

    assert [result.mode for result in results] == [request.mode for request in requests]
    assert all(result.is_estimated for result in results)
