"""房源数据库模型。"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Listing(Base):
    """租赁房源。

    硬性筛选条件采用结构化字段存储，确保预算、日期和宠物政策等条件
    可以通过确定性 SQL 查询，而不是交给大模型猜测。
    """

    __tablename__ = "listings"

    __table_args__ = (
        CheckConstraint(
            "monthly_rent > 0",
            name="ck_listings_monthly_rent_positive",
        ),
        CheckConstraint(
            "area_sqm > 0",
            name="ck_listings_area_positive",
        ),
        CheckConstraint(
            "bedrooms >= 0 AND bedrooms <= 10",
            name="ck_listings_bedrooms_range",
        ),
        CheckConstraint(
            "subway_distance_m IS NULL OR subway_distance_m >= 0",
            name="ck_listings_subway_distance_non_negative",
        ),
        CheckConstraint(
            "status IN ('available', 'reserved', 'rented', 'offline')",
            name="ck_listings_status_valid",
        ),
        # 普通 B-Tree 索引用于常见的租金筛选。
        Index("ix_listings_monthly_rent", "monthly_rent"),
        # GiST 空间索引用于附近房源和范围查询。
        Index(
            "ix_listings_location",
            "location",
            postgresql_using="gist",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # 行政区，例如“浦东新区”。
    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # 行政区下属板块，例如“张江”“金桥”。
    area: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    monthly_rent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    bedrooms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    area_sqm: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
    )

    floor: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    orientation: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    pets_allowed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    near_main_road: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    available_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    subway_distance_m: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Geography(Point, 4326) 保存经纬度，并以米作为距离计算单位。
    location: Mapped[WKBElement] = mapped_column(
        Geography(
            geometry_type="POINT",
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="available",
        server_default="available",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
