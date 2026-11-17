"""通勤计算 Service 测试。"""

from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commutes.models import CommuteCacheEntry
from app.modules.commutes.service import CommuteService
from app.providers.commute.base import (
    CommuteMode,
    CommuteRequest,
    CommuteResult,
    Coordinate,
)

LISTING_ID = UUID("00000000-0000-4000-8000-000000000001")
DESTINATION_ID = UUID("00000000-0000-4000-8000-000000000002")
CURRENT_TIME = datetime(2026, 11, 17, 8, 0, tzinfo=UTC)
CACHE_TTL = timedelta(hours=24)


def create_request() -> CommuteRequest:
    """构造固定通勤请求。"""

    return CommuteRequest(
        origin=Coordinate(
            longitude=121.602,
            latitude=31.258,
        ),
        destination=Coordinate(
            longitude=121.593,
            latitude=31.207,
        ),
        mode=CommuteMode.TRANSIT,
    )


def create_provider_result() -> CommuteResult:
    """构造固定 Provider 结果。"""

    return CommuteResult(
        mode=CommuteMode.TRANSIT,
        distance_meters=8_500,
        duration_minutes=32,
        provider="local_estimate_v1",
        is_estimated=True,
        calculated_at=CURRENT_TIME,
    )


def create_cache_entry() -> CommuteCacheEntry:
    """构造一条有效缓存记录。"""

    return CommuteCacheEntry(
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request_fingerprint="a" * 64,
        mode="transit",
        distance_meters=8_500,
        duration_minutes=32,
        provider="local_estimate_v1",
        is_estimated=True,
        calculated_at=CURRENT_TIME,
        expires_at=CURRENT_TIME + CACHE_TTL,
    )


class StubCommuteProvider:
    """记录调用次数的通勤 Provider。"""

    provider_name = "local_estimate_v1"

    def __init__(
        self,
        *,
        result: CommuteResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result or create_provider_result()
        self.error = error
        self.calculate_calls = 0

    async def calculate(
        self,
        request: CommuteRequest,
    ) -> CommuteResult:
        """返回固定结果或抛出指定异常。"""

        del request
        self.calculate_calls += 1

        if self.error is not None:
            raise self.error

        return self.result

    async def calculate_batch(
        self,
        requests: list[CommuteRequest],
    ) -> list[CommuteResult]:
        """满足 Provider 协议；本组测试不调用批量方法。"""

        return [await self.calculate(request) for request in requests]


class StubCommuteRepository:
    """按顺序返回预设查询结果的缓存 Repository。"""

    def __init__(
        self,
        lookup_results: list[CommuteCacheEntry | None],
    ) -> None:
        self.lookup_results = list(lookup_results)
        self.lookup_calls = 0
        self.upsert_calls = 0
        self.last_upserted_fingerprint: str | None = None

    async def get_valid_by_fingerprint(
        self,
        session: AsyncSession,
        *,
        request_fingerprint: str,
        current_time: datetime,
    ) -> CommuteCacheEntry | None:
        """依次返回预设缓存结果。"""

        del session, request_fingerprint, current_time
        self.lookup_calls += 1
        return self.lookup_results.pop(0)

    async def upsert(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        destination_location_id: UUID,
        request_fingerprint: str,
        result: CommuteResult,
        expires_at: datetime,
    ) -> CommuteCacheEntry:
        """模拟原子创建或刷新缓存。"""

        del session
        self.upsert_calls += 1
        self.last_upserted_fingerprint = request_fingerprint

        return CommuteCacheEntry(
            listing_id=listing_id,
            destination_location_id=destination_location_id,
            request_fingerprint=request_fingerprint,
            mode=result.mode.value,
            distance_meters=result.distance_meters,
            duration_minutes=result.duration_minutes,
            provider=result.provider,
            is_estimated=result.is_estimated,
            calculated_at=result.calculated_at,
            expires_at=expires_at,
        )


def create_session_mock() -> tuple[AsyncSession, AsyncMock]:
    """创建既满足类型检查又能断言调用的 Session Mock。"""

    session_mock = AsyncMock(spec=AsyncSession)
    return cast(AsyncSession, session_mock), session_mock


@pytest.mark.anyio
async def test_cache_hit_does_not_call_provider_or_commit() -> None:
    """缓存命中时不应重复计算或写事务。"""

    cached_entry = create_cache_entry()
    repository = StubCommuteRepository([cached_entry])
    provider = StubCommuteProvider()
    service = CommuteService(
        repository,
        provider,
        clock=lambda: CURRENT_TIME,
    )
    session, session_mock = create_session_mock()

    calculation = await service.calculate(
        session,
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request=create_request(),
    )

    assert calculation.cache_hit is True
    assert calculation.result.duration_minutes == 32
    assert calculation.expires_at == CURRENT_TIME + CACHE_TTL
    assert provider.calculate_calls == 0
    assert repository.upsert_calls == 0
    session_mock.commit.assert_not_awaited()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.anyio
async def test_cache_miss_or_expiry_recalculates_upserts_and_commits() -> None:
    """缓存不存在或已经过期时应重新计算并原子刷新。"""

    repository = StubCommuteRepository([None])
    provider = StubCommuteProvider()
    service = CommuteService(
        repository,
        provider,
        cache_ttl=CACHE_TTL,
        clock=lambda: CURRENT_TIME,
    )
    session, session_mock = create_session_mock()

    calculation = await service.calculate(
        session,
        listing_id=LISTING_ID,
        destination_location_id=DESTINATION_ID,
        request=create_request(),
    )

    assert calculation.cache_hit is False
    assert calculation.result.provider == "local_estimate_v1"
    assert calculation.expires_at == CURRENT_TIME + CACHE_TTL
    assert provider.calculate_calls == 1
    assert repository.upsert_calls == 1
    assert repository.last_upserted_fingerprint is not None
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.anyio
async def test_provider_failure_rolls_back_transaction() -> None:
    """Provider 失败时应回滚并保留原始异常。"""

    repository = StubCommuteRepository([None])
    provider = StubCommuteProvider(
        error=RuntimeError("provider unavailable"),
    )
    service = CommuteService(
        repository,
        provider,
        clock=lambda: CURRENT_TIME,
    )
    session, session_mock = create_session_mock()

    with pytest.raises(
        RuntimeError,
        match="provider unavailable",
    ):
        await service.calculate(
            session,
            listing_id=LISTING_ID,
            destination_location_id=DESTINATION_ID,
            request=create_request(),
        )

    assert repository.upsert_calls == 0
    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


def test_cache_ttl_must_be_positive() -> None:
    """零或负数 TTL 会让新缓存立即违反数据库约束。"""

    repository = StubCommuteRepository([])
    provider = StubCommuteProvider()

    with pytest.raises(
        ValueError,
        match="cache_ttl must be positive",
    ):
        CommuteService(
            repository,
            provider,
            cache_ttl=timedelta(0),
        )
