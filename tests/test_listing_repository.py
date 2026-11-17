"""房源 Repository 单元测试。"""

from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.models import Listing
from app.modules.listings.repository import ListingRepository

FIRST_LISTING_ID = UUID(
    "00000000-0000-4000-8000-000000000001",
)
SECOND_LISTING_ID = UUID(
    "00000000-0000-4000-8000-000000000002",
)


@pytest.mark.anyio
async def test_get_by_ids_uses_one_database_query() -> None:
    """多个房源 ID 应通过一次 IN 查询读取。"""

    repository = ListingRepository()
    session_mock = AsyncMock(spec=AsyncSession)
    execute_result = MagicMock()

    first_listing = Listing(id=FIRST_LISTING_ID)
    second_listing = Listing(id=SECOND_LISTING_ID)

    # 故意让数据库返回顺序与请求顺序不同，
    # 证明 Repository 不承诺 IN 查询顺序。
    execute_result.scalars.return_value.all.return_value = [
        second_listing,
        first_listing,
    ]
    session_mock.execute.return_value = execute_result

    listings = await repository.get_by_ids(
        cast(AsyncSession, session_mock),
        [
            FIRST_LISTING_ID,
            SECOND_LISTING_ID,
        ],
    )

    assert listings == [
        second_listing,
        first_listing,
    ]

    statement = session_mock.execute.await_args.args[0]
    statement_text = str(statement)

    assert "WHERE listings.id IN" in statement_text
    session_mock.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_get_by_ids_skips_query_for_empty_input() -> None:
    """空 ID 列表不应执行无意义的数据库查询。"""

    repository = ListingRepository()
    session_mock = AsyncMock(spec=AsyncSession)

    listings = await repository.get_by_ids(
        cast(AsyncSession, session_mock),
        [],
    )

    assert listings == []
    session_mock.execute.assert_not_awaited()
