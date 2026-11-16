"""地点目录 Schema 测试。"""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.modules.locations.schemas import (
    LocationResolveRequest,
    LocationResolveResponse,
    LocationResponse,
    LocationSearchParams,
)


def build_location_response() -> LocationResponse:
    """构造测试使用的标准地点。"""

    return LocationResponse(
        id=UUID("00000000-0000-4000-8000-000000000001"),
        canonical_name="张江高科技园区",
        location_type="office_area",
        district="浦东新区",
        area="张江",
        longitude=121.6000,
        latitude=31.2000,
        source="local_seed",
        aliases=["张江", "张江科学城"],
        created_at=datetime(2026, 11, 14, tzinfo=UTC),
        updated_at=datetime(2026, 11, 14, tzinfo=UTC),
    )


def test_location_search_params_strip_whitespace() -> None:
    """地点查询应该去除用户输入两侧的空格。"""

    params = LocationSearchParams(
        query="  张江高科  ",
        district="  浦东新区  ",
    )

    assert params.query == "张江高科"
    assert params.district == "浦东新区"


def test_location_resolve_request_rejects_blank_text() -> None:
    """地点解析不能接受只有空格的输入。"""

    with pytest.raises(ValidationError):
        LocationResolveRequest(text="   ")


def test_resolved_status_requires_exactly_one_match() -> None:
    """唯一解析状态必须且只能包含一个标准地点。"""

    location = build_location_response()

    response = LocationResolveResponse(
        query="张江",
        normalized_query="张江",
        status="resolved",
        matches=[location],
    )

    assert response.matches == [location]


def test_not_found_status_rejects_matches() -> None:
    """未找到状态不能同时返回候选地点。"""

    with pytest.raises(
        ValidationError,
        match="not_found status cannot contain matches",
    ):
        LocationResolveResponse(
            query="不存在的地点",
            normalized_query="不存在的地点",
            status="not_found",
            matches=[build_location_response()],
        )
