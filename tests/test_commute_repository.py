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
async def test_upsert_uses_on_conflict_without_committing() -> None:
    """缓存写入应使用 ON CONFLICT，但不能自行提交事务。"""

    repository = CommuteCacheRepository()
    session_mock = AsyncMock(spec=AsyncSession)
    execute_result = MagicMock()

    calculated_at = datetime(2026, 11, 17, 8, 0, tzinfo=UTC)
    expires_at = calculated_at + timedelta(hours=24)

    returned_entry = CommuteCacheEntry(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request_fingerprint=FINGERPRINT,
        mode="transit",
        distance_meters=8_500,
        duration_minutes=32,
        provider="local_estimate_v1",
        is_estimated=True,
        calculated_at=calculated_at,
        expires_at=expires_at,
    )

    execute_result.scalar_one.return_value = returned_entry
    session_mock.execute.return_value = execute_result

    entry = await repository.upsert(
        cast(AsyncSession, session_mock),
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request_fingerprint=FINGERPRINT,
        result=create_result(calculated_at),
        expires_at=expires_at,
    )

    assert entry is returned_entry

    statement = session_mock.execute.await_args.args[0]
    statement_text = str(statement)

    assert "INSERT INTO commute_cache_entries" in statement_text
    assert "ON CONFLICT" in statement_text
    assert "DO UPDATE SET" in statement_text
    assert "RETURNING" in statement_text

    session_mock.execute.assert_awaited_once()
    session_mock.add.assert_not_called()
    session_mock.flush.assert_not_awaited()
    session_mock.refresh.assert_not_awaited()
    session_mock.commit.assert_not_awaited()
