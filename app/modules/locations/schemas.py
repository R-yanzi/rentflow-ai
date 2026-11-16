"""地点目录 API 输入输出模型。"""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

LocationType = Literal[
    "district",
    "area",
    "metro_station",
    "office_area",
    "poi",
]

LocationResolveStatus = Literal[
    "resolved",
    "ambiguous",
    "not_found",
]


class LocationSearchParams(BaseModel):
    """地点目录搜索参数。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    query: str = Field(
        min_length=1,
        max_length=200,
        description="地点名称、简称或别名",
    )
    location_type: LocationType | None = Field(
        default=None,
        description="可选的地点类型过滤条件",
    )
    district: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="可选的行政区过滤条件",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
    )
    offset: int = Field(
        default=0,
        ge=0,
    )


class LocationResolveRequest(BaseModel):
    """把用户输入解析为标准地点的请求。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    text: str = Field(
        min_length=1,
        max_length=200,
        description="需要解析的地点文本，例如张江高科",
    )


class LocationResponse(BaseModel):
    """返回给客户端的标准地点。"""

    id: UUID
    canonical_name: str
    location_type: LocationType
    district: str
    area: str | None

    # API 返回普通经纬度，避免将 PostGIS 二进制对象泄漏给前端。
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)

    source: str
    aliases: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LocationSearchResponse(BaseModel):
    """分页地点搜索结果。"""

    items: list[LocationResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=50)
    offset: int = Field(ge=0)


class LocationResolveResponse(BaseModel):
    """地点解析结果。

    resolved 表示唯一匹配；
    ambiguous 表示存在多个候选，需要用户澄清；
    not_found 表示本地地点目录中没有匹配结果。
    """

    query: str
    normalized_query: str
    status: LocationResolveStatus
    matches: list[LocationResponse]

    @model_validator(mode="after")
    def validate_status_and_matches(self) -> Self:
        """保证解析状态与候选数量一致。"""

        match_count = len(self.matches)

        if self.status == "resolved" and match_count != 1:
            raise ValueError("resolved status requires exactly one match")

        if self.status == "ambiguous" and match_count < 2:
            raise ValueError("ambiguous status requires at least two matches")

        if self.status == "not_found" and match_count != 0:
            raise ValueError("not_found status cannot contain matches")

        return self
