"""自然语言租房需求的结构化模型。"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.modules.listings.schemas import ListingListResponse


class RentalRequirements(BaseModel):
    """从用户自然语言中提取的租房条件。

    None 表示用户没有提供该条件，模型不得擅自补充。
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    district: str | None = Field(
        default=None,
        description="用户明确指定的居住区域",
    )
    max_rent: int | None = Field(
        default=None,
        gt=0,
        description="每月最高租金，单位为人民币元",
    )
    bedrooms: int | None = Field(
        default=None,
        ge=0,
        le=10,
        description="卧室数量，开间为 0",
    )
    pets_allowed: bool | None = Field(
        default=None,
        description="是否必须允许饲养宠物",
    )
    available_before: date | None = Field(
        default=None,
        description="最晚可入住日期",
    )

    work_location: str | None = Field(
        default=None,
        description="工作地点、地铁站或办公区名称",
    )
    max_commute_minutes: int | None = Field(
        default=None,
        gt=0,
        le=240,
        description="可接受的最长单程通勤时间",
    )

    preferences: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="安静、采光好等不能直接作为硬条件的软偏好",
    )


class RequirementParseRequest(BaseModel):
    """自然语言需求解析请求。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(
        min_length=1,
        max_length=2_000,
        description="用户输入的自然语言租房需求",
    )


class NaturalLanguageSearchResponse(BaseModel):
    """自然语言房源搜索结果。"""

    requirements: RentalRequirements
    results: ListingListResponse

    # 当前阶段尚未执行的条件必须明确返回，不能悄悄忽略。
    unresolved_requirements: list[str]
