"""通勤计算 Provider 的公共契约。"""

from datetime import datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field


class CommuteMode(StrEnum):
    """项目当前支持的通勤方式。

    使用 StrEnum 可以让枚举同时保持类型安全，
    并自然序列化为 API 和数据库需要的字符串。
    """

    WALKING = "walking"
    BICYCLING = "bicycling"
    TRANSIT = "transit"
    DRIVING = "driving"


class Coordinate(BaseModel):
    """WGS84 坐标。

    GeoJSON 和 PostGIS 中始终先写经度、再写纬度，
    因此这里也使用 longitude、latitude 的固定顺序。
    """

    longitude: float = Field(
        ge=-180,
        le=180,
        description="WGS84 经度",
    )
    latitude: float = Field(
        ge=-90,
        le=90,
        description="WGS84 纬度",
    )


class CommuteRequest(BaseModel):
    """一次通勤计算请求。"""

    origin: Coordinate = Field(description="起点，一般为房源坐标")
    destination: Coordinate = Field(description="终点，一般为工作地点")
    mode: CommuteMode = Field(description="通勤方式")


class CommuteResult(BaseModel):
    """一次通勤计算的标准结果。

    无论将来使用本地估算、高德还是其他地图服务，
    业务层都只处理这个统一结构。
    """

    mode: CommuteMode
    distance_meters: int = Field(ge=0)
    duration_minutes: int = Field(ge=1)
    provider: str = Field(min_length=1, max_length=50)
    is_estimated: bool
    calculated_at: datetime


class CommuteProvider(Protocol):
    """通勤 Provider 协议。

    业务层依赖协议而不是某一家地图服务，
    后续替换实现时不需要修改搜索和排序逻辑。
    """

    # Service 在调用 Provider 前就需要生成缓存指纹，
    # 因此 Provider 必须提前公开稳定且带版本的名称。
    provider_name: str

    async def calculate(self, request: CommuteRequest) -> CommuteResult:
        """计算单条通勤路线。"""
        ...

    async def calculate_batch(
        self,
        requests: list[CommuteRequest],
    ) -> list[CommuteResult]:
        """批量计算多条通勤路线，并保持输入顺序。"""
        ...
