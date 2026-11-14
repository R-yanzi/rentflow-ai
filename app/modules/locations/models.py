"""地点目录数据库模型。"""

from datetime import datetime
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Location(Base):
    """具有标准名称和 WGS84 坐标的上海公共地点。

    Location 表示可以参与地点解析、地图展示和通勤计算的标准地点，
    不表示具体房源，也不替代 Listing 的 district 和 area 字段。
    """

    __tablename__ = "locations"

    __table_args__ = (
        CheckConstraint(
            """
            location_type IN (
                'district',
                'area',
                'metro_station',
                'office_area',
                'poi'
            )
            """,
            name="ck_locations_type_valid",
        ),
        # 同一个数据来源的稳定编号只能对应一个标准地点，
        # 使地点种子脚本可以安全地重复执行。
        UniqueConstraint(
            "source",
            "source_id",
            name="uq_locations_source_source_id",
        ),
        # 标准名称用于普通文本查询。
        Index(
            "ix_locations_normalized_name",
            "normalized_name",
        ),
        # Geography 字段使用 GiST 索引支持附近地点查询。
        Index(
            "ix_locations_location",
            "location",
            postgresql_using="gist",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    canonical_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # 搜索使用的标准化名称，例如移除两侧空格并统一常见后缀。
    normalized_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    location_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    # 当前项目首先覆盖上海，因此每个地点必须明确所属行政区。
    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # 行政区或无法归属具体板块的地点可以不填写 area。
    area: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # 项目内部统一使用 WGS84，经纬度对应 SRID 4326。
    location: Mapped[WKBElement] = mapped_column(
        Geography(
            geometry_type="POINT",
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )

    # 第一版本使用 local_seed，后续可扩展为地图 Provider。
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # 数据来源中的稳定编号，用于幂等更新和追踪来源。
    source_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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

    aliases: Mapped[list["LocationAlias"]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class LocationAlias(Base):
    """用户输入的地点别名。

    normalized_alias 用于确定性匹配。它不能全局唯一，因为不同地点
    可能拥有相同名称，此时 Service 应返回候选项让用户澄清。
    """

    __tablename__ = "location_aliases"

    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "normalized_alias",
            name="uq_location_aliases_location_normalized",
        ),
        Index(
            "ix_location_aliases_normalized_alias",
            "normalized_alias",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    location_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "locations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    alias: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    normalized_alias: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    location: Mapped[Location] = relationship(
        back_populates="aliases",
    )
