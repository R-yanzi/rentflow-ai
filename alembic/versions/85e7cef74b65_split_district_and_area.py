"""split district and area

Revision ID: 85e7cef74b65
Revises: 7c688a753de6
Create Date: 2026-11-14 12:37:02.780285

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "85e7cef74b65"
down_revision: str | Sequence[str] | None = "7c688a753de6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """拆分行政区和板块，并迁移已有合成数据。"""

    # 先允许为空，否则已有 301 条数据无法直接增加非空字段。
    op.add_column(
        "listings",
        sa.Column("area", sa.String(length=100), nullable=True),
    )

    # 原 district 实际保存的是张江、川沙等板块。
    op.execute(
        sa.text(
            """
            UPDATE listings
            SET area = district
            """
        )
    )

    # 当前合成数据全部位于浦东新区。
    op.execute(
        sa.text(
            """
            UPDATE listings
            SET district = '浦东新区'
            """
        )
    )

    # 数据回填完成后，再建立非空约束。
    op.alter_column(
        "listings",
        "area",
        existing_type=sa.String(length=100),
        nullable=False,
    )

    op.create_index(
        op.f("ix_listings_area"),
        "listings",
        ["area"],
        unique=False,
    )


def downgrade() -> None:
    """恢复旧结构时，把板块值写回 district。"""

    op.execute(
        sa.text(
            """
            UPDATE listings
            SET district = area
            """
        )
    )

    op.drop_index(
        op.f("ix_listings_area"),
        table_name="listings",
    )
    op.drop_column("listings", "area")
