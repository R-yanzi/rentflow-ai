"""通勤计算结果缓存模型。"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CommuteCacheEntry(Base):
    """房源到标准地点的通勤计算缓存。

    缓存记录既保存业务关联 ID，也保存请求指纹：
    ID 用于追踪结果属于哪个房源和目的地；
    指纹用于防止坐标、交通方式或算法版本变化后错误复用旧结果。

    同一个请求指纹只保留一条当前结果。
    缓存过期后通过原子 Upsert 更新计算结果和过期时间。
    """

    __tablename__ = "commute_cache_entries"

    __table_args__ = (
        CheckConstraint(
            """
            mode IN (
                'walking',
                'bicycling',
                'transit',
                'driving'
            )
            """,
            name="ck_commute_cache_entries_mode_valid",
        ),
        CheckConstraint(
            "distance_meters >= 0",
            name="ck_commute_cache_entries_distance_non_negative",
        ),
        CheckConstraint(
            "duration_minutes > 0",
            name="ck_commute_cache_entries_duration_positive",
        ),
        CheckConstraint(
            "expires_at > calculated_at",
            name="ck_commute_cache_entries_expiry_after_calculation",
        ),
        UniqueConstraint(
            "request_fingerprint",
            name="uq_commute_cache_entries_request_fingerprint",
        ),
        # 后续用于查看某套房源到某个目的地的不同通勤方式。
        Index(
            "ix_commute_cache_entries_listing_destination",
            "listing_id",
            "destination_location_id",
        ),
        # 后续清理任务可以快速定位过期记录。
        Index(
            "ix_commute_cache_entries_expires_at",
            "expires_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    listing_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "listings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    destination_location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "locations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # SHA-256 十六进制摘要固定为 64 个字符。
    request_fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    distance_meters: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # 例如 local_estimate_v1。版本变化后会生成不同指纹。
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    is_estimated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
