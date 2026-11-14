"""合成房源生成规则测试。"""

import random

from scripts.seed_listings import AREA_RANGES, generate_listing


def test_generated_listing_is_deterministic() -> None:
    """相同随机种子和序号应生成相同房源。"""

    first = generate_listing(
        random.Random(2026),
        index=10,
        seed=2026,
    )
    second = generate_listing(
        random.Random(2026),
        index=10,
        seed=2026,
    )

    assert first.id == second.id
    assert first.title == second.title
    assert first.monthly_rent == second.monthly_rent
    assert first.area_sqm == second.area_sqm
    assert first.available_date == second.available_date


def test_generated_listing_obeys_business_constraints() -> None:
    """生成的户型、面积、租金和地铁距离必须合理。"""

    listing = generate_listing(
        random.Random(2026),
        index=0,
        seed=2026,
    )

    min_area, max_area = AREA_RANGES[listing.bedrooms]

    assert min_area <= float(listing.area_sqm) <= max_area
    assert listing.monthly_rent > 0
    assert listing.subway_distance_m is not None
    assert listing.subway_distance_m >= 0
    assert listing.status == "available"
    assert listing.district == "浦东新区"
    assert listing.area in {
        "张江",
        "金桥",
        "唐镇",
        "北蔡",
        "川沙",
    }
