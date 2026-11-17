"""无需外部地图 API 的本地通勤估算实现。"""

from dataclasses import dataclass
from datetime import UTC, datetime
from math import asin, ceil, cos, radians, sin, sqrt

from app.providers.commute.base import (
    CommuteMode,
    CommuteRequest,
    CommuteResult,
    Coordinate,
)

EARTH_RADIUS_METERS = 6_371_000


@dataclass(frozen=True, slots=True)
class ModeEstimateConfig:
    """某种交通方式的估算参数。

    detour_factor 用于把直线距离修正为近似道路距离；
    fixed_minutes 用于表示等车、停车等固定时间。
    """

    detour_factor: float
    speed_kmh: float
    fixed_minutes: float


MODE_CONFIGS: dict[CommuteMode, ModeEstimateConfig] = {
    CommuteMode.WALKING: ModeEstimateConfig(
        detour_factor=1.20,
        speed_kmh=4.8,
        fixed_minutes=0,
    ),
    CommuteMode.BICYCLING: ModeEstimateConfig(
        detour_factor=1.25,
        speed_kmh=14,
        fixed_minutes=2,
    ),
    CommuteMode.TRANSIT: ModeEstimateConfig(
        detour_factor=1.35,
        speed_kmh=25,
        fixed_minutes=8,
    ),
    CommuteMode.DRIVING: ModeEstimateConfig(
        detour_factor=1.25,
        speed_kmh=30,
        fixed_minutes=5,
    ),
}


def haversine_distance(
    origin: Coordinate,
    destination: Coordinate,
) -> float:
    """使用 Haversine 公式计算两点之间的球面直线距离。

    返回值单位为米。这只是估算的基础距离，
    不能直接冒充真实道路或轨道交通距离。
    """

    origin_latitude = radians(origin.latitude)
    destination_latitude = radians(destination.latitude)

    latitude_delta = destination_latitude - origin_latitude
    longitude_delta = radians(destination.longitude - origin.longitude)

    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(origin_latitude) * cos(destination_latitude) * sin(longitude_delta / 2) ** 2
    )

    central_angle = 2 * asin(sqrt(haversine))
    return EARTH_RADIUS_METERS * central_angle


class LocalEstimateCommuteProvider:
    """基于距离、绕行系数和平均速度的本地估算器。

    该实现适合开发和演示，不代表真实路况。
    返回结果始终明确标记为 estimated。
    """

    provider_name = "local_estimate_v1"

    async def calculate(
        self,
        request: CommuteRequest,
    ) -> CommuteResult:
        """估算单条通勤路线。"""

        config = MODE_CONFIGS[request.mode]
        straight_distance = haversine_distance(
            request.origin,
            request.destination,
        )

        route_distance = straight_distance * config.detour_factor
        travel_minutes = route_distance / 1000 / config.speed_kmh * 60
        duration_minutes = max(
            1,
            ceil(travel_minutes + config.fixed_minutes),
        )

        return CommuteResult(
            mode=request.mode,
            distance_meters=round(route_distance),
            duration_minutes=duration_minutes,
            provider=self.provider_name,
            is_estimated=True,
            calculated_at=datetime.now(UTC),
        )

    async def calculate_batch(
        self,
        requests: list[CommuteRequest],
    ) -> list[CommuteResult]:
        """依照请求顺序批量返回估算结果。"""

        return [await self.calculate(request) for request in requests]
