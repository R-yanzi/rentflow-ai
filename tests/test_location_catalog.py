"""上海地点种子目录测试。"""

from app.modules.locations.normalization import normalize_location_text
from scripts.location_catalog import LOCATION_CATALOG
from scripts.seed_locations import (
    build_location,
    location_id_for,
)


def test_location_catalog_has_unique_source_ids() -> None:
    """稳定来源编号不能重复。"""

    source_ids = [
        location.source_id
        for location in LOCATION_CATALOG
    ]

    assert len(source_ids) == len(set(source_ids))


def test_location_catalog_coordinates_are_in_shanghai_region() -> None:
    """演示地点坐标应位于上海附近。"""

    for location in LOCATION_CATALOG:
        assert 120.8 <= location.longitude <= 122.0
        assert 30.6 <= location.latitude <= 31.9


def test_location_catalog_aliases_are_valid_and_unique_per_location() -> None:
    """同一地点不能保存重复或无效别名。"""

    for location in LOCATION_CATALOG:
        normalized_aliases = [
            normalize_location_text(alias)
            for alias in location.aliases
        ]

        assert all(normalized_aliases)
        assert len(normalized_aliases) == len(
            set(normalized_aliases)
        )


def test_location_catalog_contains_intentional_ambiguity() -> None:
    """“张江”应能演示多个标准地点候选。"""

    matching_locations = [
        location
        for location in LOCATION_CATALOG
        if "张江" in location.aliases
    ]

    assert len(matching_locations) >= 2

def test_location_ids_are_deterministic() -> None:
    """相同 source_id 必须生成相同 UUID。"""

    first = location_id_for("area-zhangjiang")
    second = location_id_for("area-zhangjiang")

    assert first == second


def test_build_location_includes_canonical_name_as_alias() -> None:
    """标准名称应该自动加入可搜索别名集合。"""

    seed = LOCATION_CATALOG[0]
    location = build_location(seed)

    normalized_aliases = {
        alias.normalized_alias
        for alias in location.aliases
    }

    assert location.normalized_name == normalize_location_text(
        seed.canonical_name,
    )
    assert normalize_location_text(
        seed.canonical_name,
    ) in normalized_aliases