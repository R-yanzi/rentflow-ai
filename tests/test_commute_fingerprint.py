"""通勤缓存请求指纹测试。"""

from uuid import UUID

from app.modules.commutes.fingerprint import build_commute_fingerprint
from app.providers.commute.base import (
    CommuteMode,
    CommuteRequest,
    Coordinate,
)

LISTING_ID = UUID("00000000-0000-4000-8000-000000000001")
DESTINATION_ID = UUID("00000000-0000-4000-8000-000000000002")


def create_request(
    *,
    mode: CommuteMode = CommuteMode.TRANSIT,
    origin_longitude: float = 121.602,
) -> CommuteRequest:
    """构造稳定的测试通勤请求。"""

    return CommuteRequest(
        origin=Coordinate(
            longitude=origin_longitude,
            latitude=31.258,
        ),
        destination=Coordinate(
            longitude=121.593,
            latitude=31.207,
        ),
        mode=mode,
    )


def test_identical_requests_have_identical_fingerprints() -> None:
    """相同请求必须稳定生成相同指纹。"""

    first = build_commute_fingerprint(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request=create_request(origin_longitude=121.602),
        provider="local_estimate_v1",
    )
    second = build_commute_fingerprint(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request=create_request(origin_longitude=121.602000),
        provider="local_estimate_v1",
    )

    assert first == second
    assert len(first) == 64


def test_transport_mode_changes_fingerprint() -> None:
    """不同交通方式不能复用同一条缓存。"""

    transit = build_commute_fingerprint(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request=create_request(mode=CommuteMode.TRANSIT),
        provider="local_estimate_v1",
    )
    driving = build_commute_fingerprint(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request=create_request(mode=CommuteMode.DRIVING),
        provider="local_estimate_v1",
    )

    assert transit != driving


def test_coordinate_or_provider_change_invalidates_fingerprint() -> None:
    """坐标或 Provider 版本变化后必须生成新指纹。"""

    original = build_commute_fingerprint(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request=create_request(),
        provider="local_estimate_v1",
    )
    moved_listing = build_commute_fingerprint(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request=create_request(origin_longitude=121.603),
        provider="local_estimate_v1",
    )
    upgraded_provider = build_commute_fingerprint(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request=create_request(),
        provider="local_estimate_v2",
    )

    assert original != moved_listing
    assert original != upgraded_provider
