"""汇总所有 ORM 模型，供 Alembic 自动检测。"""

from app.db.base import Base
from app.modules.listings.models import Listing
from app.modules.locations.models import Location, LocationAlias

# 只有导入模型后，对应的 Table 才会注册到 Base.metadata，
# Alembic 才能自动检测这些表。
__all__ = [
    "Base",
    "Listing",
    "Location",
    "LocationAlias",
]
