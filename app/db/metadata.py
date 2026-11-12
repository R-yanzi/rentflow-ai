"""汇总所有 ORM 模型，供 Alembic 自动检测。"""

from app.db.base import Base
from app.modules.listings.models import Listing

# 导出 Listing 可以明确告诉 Ruff：这个导入是有意为之。
# 导入模型后，它对应的 Table 才会注册到 Base.metadata。
__all__ = ["Base", "Listing"]
