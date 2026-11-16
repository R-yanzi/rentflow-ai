"""地点模块依赖装配。"""

from functools import lru_cache

from app.modules.locations.repository import LocationRepository
from app.modules.locations.service import LocationService


@lru_cache
def get_location_service() -> LocationService:
    """创建并缓存无状态的地点业务服务。"""

    return LocationService(
        LocationRepository(),
    )