"""通勤 API Schema 测试。"""

from uuid import UUID

import pytest
from pydantic import ValidationError

from app.modules.commutes.schemas import CommuteBatchRequest
from app.providers.commute.base import CommuteMode

DESTINATION_ID = UUID("00000000-0000-4000-8000-000000000099")


def listing_id(number: int) -> UUID:
    """根据整数生成稳定测试 UUID。"""

    return UUID(
        f"00000000-0000-4000-8000-{number:012d}",
    )


def test_batch_request_accepts_valid_business_ids() -> None:
    """合法请求应保留房源顺序和交通方式。"""

    request = CommuteBatchRequest(
        listing_ids=[
            listing_id(1),
            listing_id(2),
        ],
        destination_location_id=DESTINATION_ID,
        mode=CommuteMode.TRANSIT,
    )

    assert request.listing_ids == [
        listing_id(1),
        listing_id(2),
    ]
    assert request.destination_location_id == DESTINATION_ID
    assert request.mode is CommuteMode.TRANSIT


def test_batch_request_rejects_empty_listing_ids() -> None:
    """批量请求至少需要一套房源。"""

    with pytest.raises(ValidationError):
        CommuteBatchRequest(
            listing_ids=[],
            destination_location_id=DESTINATION_ID,
            mode=CommuteMode.TRANSIT,
        )


def test_batch_request_rejects_duplicate_listing_ids() -> None:
    """重复房源 ID 会造成重复计算和含糊的结果顺序。"""

    duplicate_id = listing_id(1)

    with pytest.raises(
        ValidationError,
        match="listing_ids must not contain duplicates",
    ):
        CommuteBatchRequest(
            listing_ids=[
                duplicate_id,
                duplicate_id,
            ],
            destination_location_id=DESTINATION_ID,
            mode=CommuteMode.TRANSIT,
        )


def test_batch_request_limits_batch_size() -> None:
    """单次请求最多允许 50 套房源。"""

    with pytest.raises(ValidationError):
        CommuteBatchRequest(
            listing_ids=[listing_id(number) for number in range(1, 52)],
            destination_location_id=DESTINATION_ID,
            mode=CommuteMode.TRANSIT,
        )
