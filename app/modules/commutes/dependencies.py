"""通勤模块依赖装配。"""

from functools import lru_cache

from app.modules.commutes.batch_service import CommuteBatchService
from app.modules.commutes.repository import CommuteCacheRepository
from app.modules.commutes.service import CommuteService
from app.modules.listings.repository import ListingRepository
from app.modules.locations.repository import LocationRepository
from app.providers.commute.local import LocalEstimateCommuteProvider


@lru_cache
def get_commute_batch_service() -> CommuteBatchService:
    """创建并缓存无状态的批量通勤业务服务。"""

    calculator = CommuteService(
        CommuteCacheRepository(),
        LocalEstimateCommuteProvider(),
    )

    return CommuteBatchService(
        ListingRepository(),
        LocationRepository(),
        calculator,
    )
