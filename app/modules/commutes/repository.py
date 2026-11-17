"""通勤缓存数据访问层。"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commutes.models import CommuteCacheEntry
from app.providers.commute.base import CommuteResult


class CommuteCacheRepository:
    """封装通勤缓存的数据库读写。

    Repository 只负责持久化，不决定缓存有效期，
    不调用 Provider，也不提交或回滚事务。
    """

    async def get_valid_by_fingerprint(
        self,
        session: AsyncSession,
        *,
        request_fingerprint: str,
        current_time: datetime,
    ) -> CommuteCacheEntry | None:
        """查询一条尚未过期的缓存。

        过期判断直接进入 SQL，使所有调用方共享同一条规则，
        避免先读取记录、再在 Python 中重复判断。
        """

        statement = select(CommuteCacheEntry).where(
            CommuteCacheEntry.request_fingerprint == request_fingerprint,
            CommuteCacheEntry.expires_at > current_time,
        )

        result = await session.execute(statement)

        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        *,
        listing_id: UUID,
        destination_location_id: UUID,
        request_fingerprint: str,
        result: CommuteResult,
        expires_at: datetime,
    ) -> CommuteCacheEntry:
        """创建缓存记录，但不提交事务。

        事务边界由 Service 控制，使“Provider 计算 + 缓存写入”
        能够按照完整业务流程统一处理异常。
        """

        entry = CommuteCacheEntry(
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

        session.add(entry)

        # flush 会执行 INSERT 并触发唯一约束，
        # 但不会在 Repository 内提前提交事务。
        await session.flush()
        await session.refresh(entry)

        return entry
