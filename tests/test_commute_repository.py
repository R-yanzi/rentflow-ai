"""通勤缓存 Repository 单元测试。"""

from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commutes.models import CommuteCacheEntry
from app.modules.commutes.repository import CommuteCacheRepository
from app.providers.commute.base import CommuteMode, CommuteResult

LISTING_ID = UUID("00000000-0000-4000-8000-000000000001")
DESTINATION_ID = UUID("00000000-0000-4000-8000-000000000002")
FINGERPRINT = "a" * 64


def create_result(calculated_at: datetime) -> CommuteResult:
    """构造固定的 Provider 计算结果。"""

    return CommuteResult(
        mode=CommuteMode.TRANSIT,
        distance_meters=8_500,
        duration_minutes=32,
        provider="local_estimate_v1",
        is_estimated=True,
        calculated_at=calculated_at,
    )


@pytest.mark.anyio
async def test_get_valid_cache_filters_fingerprint_and_expiry() -> None:
    """缓存查询必须同时限制请求指纹和过期时间。"""

    repository = CommuteCacheRepository()
    session_mock = AsyncMock(spec=AsyncSession)
    execute_result = MagicMock()

    cached_entry = CommuteCacheEntry(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request_fingerprint=FINGERPRINT,
        mode="transit",
        distance_meters=8_500,
        duration_minutes=32,
        provider="local_estimate_v1",
        is_estimated=True,
        calculated_at=datetime(2026, 11, 17, 8, 0, tzinfo=UTC),
        expires_at=datetime(2026, 11, 18, 8, 0, tzinfo=UTC),
    )

    execute_result.scalar_one_or_none.return_value = cached_entry
    session_mock.execute.return_value = execute_result

    current_time = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)

    result = await repository.get_valid_by_fingerprint(
        cast(AsyncSession, session_mock),
        request_fingerprint=FINGERPRINT,
        current_time=current_time,
    )

    assert result is cached_entry

    statement = session_mock.execute.await_args.args[0]
    statement_text = str(statement)

    assert "request_fingerprint" in statement_text
    assert "expires_at >" in statement_text
    session_mock.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_create_maps_provider_result_without_committing() -> None:
    """Repository 应映射结果并 flush，但不能自行提交事务。"""

    repository = CommuteCacheRepository()
    session_mock = AsyncMock(spec=AsyncSession)

    calculated_at = datetime(2026, 11, 17, 8, 0, tzinfo=UTC)
    expires_at = calculated_at + timedelta(hours=24)

    entry = await repository.create(
        cast(AsyncSession, session_mock),
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request_fingerprint=FINGERPRINT,
        result=create_result(calculated_at),
        expires_at=expires_at,
    )

    assert entry.listing_id == LISTING_ID
    assert entry.destination_location_id == DESTINATION_ID
    assert entry.request_fingerprint == FINGERPRINT
    assert entry.mode == "transit"
    assert entry.distance_meters == 8_500
    assert entry.duration_minutes == 32
    assert entry.provider == "local_estimate_v1"
    assert entry.is_estimated is True
    assert entry.calculated_at == calculated_at
    assert entry.expires_at == expires_at

    session_mock.add.assert_called_once_with(entry)
    session_mock.flush.assert_awaited_once()
    session_mock.refresh.assert_awaited_once_with(entry)
    session_mock.commit.assert_not_awaited()
