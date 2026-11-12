"""房源 Schema 单元测试。"""

import pytest
from pydantic import ValidationError

from app.modules.listings.schemas import ListingSearchParams


def test_location_filter_requires_all_three_parameters() -> None:
    """位置搜索必须同时提供经度、纬度和半径。"""

    with pytest.raises(
        ValidationError,
        match="must be provided together",
    ):
        ListingSearchParams(longitude=121.606)


def test_location_filter_accepts_complete_parameters() -> None:
    """完整位置参数应该通过校验。"""

    params = ListingSearchParams(
        longitude=121.606,
        latitude=31.204,
        radius_m=3_000,
    )

    assert params.longitude == 121.606
    assert params.latitude == 31.204
    assert params.radius_m == 3_000


def test_search_pagination_has_upper_limit() -> None:
    """单次查询数量不能超过 100，避免无界查询。"""

    with pytest.raises(ValidationError):
        ListingSearchParams(limit=101)
