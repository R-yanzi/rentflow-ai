"""通勤缓存数据访问层。"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
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
        """原子创建或刷新缓存，但不提交事务。

        PostgreSQL ON CONFLICT 同时处理两种情况：

        1. 已过期记录仍占用唯一指纹时，更新原记录；
        2. 两个并发请求同时写入时，由数据库原子合并。
        """

        statement = (
            insert(CommuteCacheEntry)
            .values(
                id=uuid4(),
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
            .on_conflict_do_update(
                constraint="uq_commute_cache_entries_request_fingerprint",
                set_={
                    "listing_id": listing_id,
                    "destination_location_id": destination_location_id,
                    "mode": result.mode.value,
                    "distance_meters": result.distance_meters,
                    "duration_minutes": result.duration_minutes,
                    "provider": result.provider,
                    "is_estimated": result.is_estimated,
                    "calculated_at": result.calculated_at,
                    "expires_at": expires_at,
                },
            )
            .returning(CommuteCacheEntry)
        )

        execution_result = await session.execute(statement)

        return execution_result.scalar_one()
