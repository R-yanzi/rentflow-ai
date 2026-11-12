"""自然语言需求到数据库条件的映射测试。"""

from app.modules.search.schemas import RentalRequirements
from app.modules.search.service import (
    build_listing_search_params,
    collect_unresolved_requirements,
)


def test_requirements_are_mapped_to_hard_filters() -> None:
    """确定性条件应该被转换成数据库查询参数。"""

    requirements = RentalRequirements(
        max_rent=5_000,
        bedrooms=1,
        pets_allowed=True,
        work_location="张江",
        max_commute_minutes=40,
        preferences=["安静"],
    )

    params = build_listing_search_params(requirements)

    assert params.max_rent == 5_000
    assert params.bedrooms == 1
    assert params.pets_allowed is True

    # 工作地点和软偏好尚不能直接转成 SQL 条件。
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
