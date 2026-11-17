"""通勤计算业务服务。"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commutes.fingerprint import build_commute_fingerprint
from app.modules.commutes.models import CommuteCacheEntry
from app.modules.commutes.schemas import CommuteCalculation
from app.providers.commute.base import (
    CommuteMode,
    CommuteProvider,
    CommuteRequest,
    CommuteResult,
)


class CommuteCacheRepositoryProtocol(Protocol):
    """CommuteService 依赖的缓存数据访问接口。

    Service 依赖协议，测试时可以使用不连接数据库的 Stub。
    """

    async def get_valid_by_fingerprint(
        self,
        session: AsyncSession,
        *,
        request_fingerprint: str,
        current_time: datetime,
    ) -> CommuteCacheEntry | None: ...

    async def upsert(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        destination_location_id: UUID,
        request_fingerprint: str,
        result: CommuteResult,
        expires_at: datetime,
    ) -> CommuteCacheEntry: ...


def utc_now() -> datetime:
    """返回带 UTC 时区的当前时间。"""

    return datetime.now(UTC)


class CommuteService:
    """协调缓存、Provider 与事务边界。"""

    def __init__(
        self,
        repository: CommuteCacheRepositoryProtocol,
        provider: CommuteProvider,
        *,
        cache_ttl: timedelta = timedelta(hours=24),
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        """创建通勤服务。

        clock 可以在测试中替换为固定时间，
        避免测试依赖真实系统时钟。
        """

        if cache_ttl <= timedelta(0):
            raise ValueError("cache_ttl must be positive")

        self._repository = repository
        self._provider = provider
        self._cache_ttl = cache_ttl
        self._clock = clock

    async def calculate(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        destination_location_id: UUID,
        request: CommuteRequest,
    ) -> CommuteCalculation:
        """返回缓存结果，或调用 Provider 计算并写入缓存。"""

        current_time = self._clock()
        request_fingerprint = build_commute_fingerprint(
            listing_id=listing_id,
            destination_location_id=destination_location_id,
            request=request,
            provider=self._provider.provider_name,
        )

        cached_entry = await self._repository.get_valid_by_fingerprint(
            session,
            request_fingerprint=request_fingerprint,
            current_time=current_time,
        )

        if cached_entry is not None:
            return self._to_calculation(
                cached_entry,
                cache_hit=True,
            )

        try:
            provider_result = await self._provider.calculate(request)
            expires_at = provider_result.calculated_at + self._cache_ttl

            created_entry = await self._repository.upsert(
                session,
                listing_id=listing_id,
                destination_location_id=destination_location_id,
                request_fingerprint=request_fingerprint,
                result=provider_result,
                expires_at=expires_at,
            )

            await session.commit()

            return self._to_calculation(
                created_entry,
                cache_hit=False,
            )
        except Exception:
            # Provider 或数据库写入失败时显式回滚，
            # 确保当前 Session 不会停留在失败事务中。
            await session.rollback()
            raise

    @staticmethod
    def _to_calculation(
        entry: CommuteCacheEntry,
        *,
        cache_hit: bool,
    ) -> CommuteCalculation:
        """把 ORM 缓存记录转换为业务输出。"""

        result = CommuteResult(
            mode=CommuteMode(entry.mode),
            distance_meters=entry.distance_meters,
            duration_minutes=entry.duration_minutes,
            provider=entry.provider,
            is_estimated=entry.is_estimated,
            calculated_at=entry.calculated_at,
        )

        return CommuteCalculation(
            result=result,
            cache_hit=cache_hit,
            expires_at=entry.expires_at,
        )
