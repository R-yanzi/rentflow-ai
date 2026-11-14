"""自然语言需求到数据库条件的映射测试。"""

from app.modules.search.schemas import RentalRequirements
from app.modules.search.service import (
    build_listing_search_params,
    collect_unresolved_requirements,
)


def test_requirements_are_mapped_to_hard_filters() -> None:
    """行政区、板块和其他硬条件应该转换成数据库查询参数。"""

    requirements = RentalRequirements(
        district="浦东",
        area="张江",
        max_rent=5_000,
        bedrooms=1,
        pets_allowed=True,
        work_location="陆家嘴",
        max_commute_minutes=40,
        preferences=["安静"],
    )

    params = build_listing_search_params(requirements)

    # 常见别名应在进入数据库查询之前规范化。
    assert params.district == "浦东新区"
    assert params.area == "张江"
    assert params.max_rent == 5_000
    assert params.bedrooms == 1
    assert params.pets_allowed is True

    assert params.longitude is None
    assert params.radius_m is None

def test_unresolved_requirements_are_explicit() -> None:
    """系统不能悄悄忽略尚未支持的需求。"""

    requirements = RentalRequirements(
        work_location="张江",
        max_commute_minutes=40,
        preferences=["安静", "采光好"],
    )

    unresolved = collect_unresolved_requirements(requirements)

    assert unresolved == [
        "work_location",
        "max_commute_minutes",
        "preferences",
    ]
