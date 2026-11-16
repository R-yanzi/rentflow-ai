"""地点目录数据访问层。"""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.locations.models import Location, LocationAlias
from app.modules.locations.schemas import LocationSearchParams


class LocationRepository:
    """封装地点目录查询。

    Repository 只负责构造和执行数据库查询，
    不决定匹配结果属于唯一匹配、歧义还是未找到。
    """

    async def get_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
    ) -> Location | None:
        """根据主键查询地点，并预加载其别名。"""

        statement = (
            select(Location)
            .options(selectinload(Location.aliases))
            .where(
                Location.id == location_id,
                Location.is_active.is_(True),
            )
        )

        result = await session.execute(statement)

        return result.scalar_one_or_none()

    async def find_exact(
        self,
        session: AsyncSession,
        normalized_query: str,
    ) -> list[Location]:
        """按标准名称或别名执行精确匹配。

        同一个地点可能被多个别名命中，因此需要使用 distinct
        和 unique 去除关联查询产生的重复 ORM 对象。
        """

        statement = (
            select(Location)
            .outerjoin(
                LocationAlias,
                LocationAlias.location_id == Location.id,
            )
            .options(selectinload(Location.aliases))
            .where(
                Location.is_active.is_(True),
                or_(
                    Location.normalized_name == normalized_query,
                    LocationAlias.normalized_alias == normalized_query,
                ),
            )
            .distinct()
            .order_by(
                Location.canonical_name.asc(),
                Location.id.asc(),
            )
        )

        result = await session.execute(statement)

        return list(result.scalars().unique().all())

    async def search(
        self,
        session: AsyncSession,
        params: LocationSearchParams,
        normalized_query: str,
    ) -> tuple[list[Location], int]:
        """按标准名称或别名进行分页模糊搜索。"""

        # autoescape=True 会转义用户输入中的 SQL LIKE 通配符，
        # 防止 % 或 _ 被意外解释为任意字符。
        name_condition = or_(
            Location.normalized_name.contains(
                normalized_query,
                autoescape=True,
            ),
            LocationAlias.normalized_alias.contains(
                normalized_query,
                autoescape=True,
            ),
        )

        conditions = [
            Location.is_active.is_(True),
            name_condition,
        ]

        if params.location_type is not None:
            conditions.append(
                Location.location_type == params.location_type,
            )

        if params.district is not None:
            conditions.append(
                Location.district == params.district,
            )

        # 一个地点可能拥有多个命中的别名，因此总数必须按地点 ID 去重。
        count_statement = (
            select(func.count(func.distinct(Location.id)))
            .select_from(Location)
            .outerjoin(
                LocationAlias,
                LocationAlias.location_id == Location.id,
            )
            .where(*conditions)
        )
        total = await session.scalar(count_statement)

        search_statement = (
            select(Location)
            .outerjoin(
                LocationAlias,
                LocationAlias.location_id == Location.id,
            )
            .options(selectinload(Location.aliases))
            .where(*conditions)
            .distinct()
            .order_by(
                Location.canonical_name.asc(),
                Location.id.asc(),
            )
            .limit(params.limit)
            .offset(params.offset)
        )

        result = await session.execute(search_statement)
        locations = list(result.scalars().unique().all())

        return locations, int(total or 0)