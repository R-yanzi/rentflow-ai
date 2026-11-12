"""房源模块依赖装配。"""

from functools import lru_cache

from app.modules.listings.repository import ListingRepository
from app.modules.listings.service import ListingService


@lru_cache
def get_listing_service() -> ListingService:
    """创建并缓存无状态的房源业务服务。"""
    return ListingService(ListingRepository())
