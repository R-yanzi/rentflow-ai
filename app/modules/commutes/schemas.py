"""通勤业务输入输出模型。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.providers.commute.base import (
    CommuteMode,
    CommuteResult,
)


class CommuteCalculation(BaseModel):
    """一次通勤计算及其缓存状态。

    result 是与具体地图厂商无关的标准结果；
    cache_hit 用于日志、监控和后续 API 展示；
    expires_at 表示本结果何时需要重新计算。
    """

    result: CommuteResult
    cache_hit: bool
    expires_at: datetime


class CommuteBatchRequest(BaseModel):
    """批量计算多套房源到同一标准地点的通勤信息。"""

    listing_ids: list[UUID] = Field(
        min_length=1,
        max_length=50,
        description="需要计算的房源 ID，最多 50 套",
    )
    destination_location_id: UUID = Field(
        description="标准地点目录中的目的地 ID",
    )
    mode: CommuteMode = Field(
        description="统一应用于本批房源的通勤方式",
    )

    @field_validator("listing_ids")
    @classmethod
    def validate_unique_listing_ids(
        cls,
        listing_ids: list[UUID],
    ) -> list[UUID]:
        """拒绝重复房源，避免重复计算和含糊的返回顺序。"""

        if len(listing_ids) != len(set(listing_ids)):
            raise ValueError("listing_ids must not contain duplicates")

        return listing_ids


class ListingCommuteCalculation(BaseModel):
    """一套房源对应的通勤计算结果。"""

    listing_id: UUID
    calculation: CommuteCalculation


class CommuteBatchResponse(BaseModel):
    """保持请求房源顺序的批量通勤结果。"""

    destination_location_id: UUID
    mode: CommuteMode
    items: list[ListingCommuteCalculation]
