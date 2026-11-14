"""房源 API 输入输出模型。"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

ListingStatus = Literal["available", "reserved", "rented", "offline"]


class ListingCreate(BaseModel):
    """创建房源时由客户端提交的数据。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    monthly_rent: int = Field(gt=0)
    bedrooms: int = Field(ge=0, le=10)
    area_sqm: Decimal = Field(gt=0, max_digits=7, decimal_places=2)

    floor: int | None = None
    orientation: str | None = Field(default=None, max_length=20)
    pets_allowed: bool = False
    near_main_road: bool = False
    available_date: date
    subway_distance_m: int | None = Field(default=None, ge=0)
    description: str = Field(min_length=1)

    # 经度范围为 -180～180，纬度范围为 -90～90。
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)

    district: str = Field(min_length=1, max_length=100)
    area: str = Field(min_length=1, max_length=100)


class ListingResponse(BaseModel):
    """返回给客户端的房源详情。"""

    id: UUID
    title: str
    monthly_rent: int
    bedrooms: int
    area_sqm: Decimal
    floor: int | None
    orientation: str | None
    pets_allowed: bool
    near_main_road: bool
    available_date: date
    subway_distance_m: int | None
    description: str
    longitude: float
    latitude: float
    status: ListingStatus
    created_at: datetime
    updated_at: datetime

    # 普通详情查询没有参考点，因此距离可以为空。
    distance_m: float | None = None

    district: str
    area: str


class ListingSearchParams(BaseModel):
    """房源搜索条件。

    这些条件属于确定性业务规则，必须转换成 SQL，
    不能交给大模型自行判断。
    """

    max_rent: int | None = Field(default=None, gt=0)
    bedrooms: int | None = Field(default=None, ge=0, le=10)
    pets_allowed: bool | None = None
    available_before: date | None = None

    # 空间筛选参数是可选的，但必须成组出现。
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    radius_m: int | None = Field(default=None, gt=0, le=100_000)

    district: str | None = None
    area: str | None = None

    @model_validator(mode="after")
    def validate_location_filter(self) -> Self:
        """经度、纬度和搜索半径必须同时提供或同时省略。"""
        location_values = (
            self.longitude,
            self.latitude,
            self.radius_m,
        )

        if any(value is not None for value in location_values) and not all(
            value is not None for value in location_values
        ):
            raise ValueError("longitude, latitude and radius_m must be provided together")

        return self

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ListingListResponse(BaseModel):
    """分页房源列表。"""

    items: list[ListingResponse]
    total: int
    limit: int
    offset: int
