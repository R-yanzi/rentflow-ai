"""房源数据访问层。"""

from typing import cast
from uuid import UUID

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement, WKTElement
from sqlalchemy import Float, func, literal, select
from sqlalchemy import cast as sql_cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.modules.listings.models import Listing
from app.modules.listings.schemas import ListingCreate, ListingSearchParams


class ListingRepository:
    """封装房源相关的数据库操作。

    Repository 只负责持久化，不负责 HTTP 异常和业务响应格式。
    """

    async def create(
        self,
        session: AsyncSession,
        data: ListingCreate,
    ) -> Listing:
        """创建房源，但不在这里提交事务。"""

        # WKT 的 POINT 顺序是“经度 纬度”，不能写反。
        location = WKTElement(
            f"POINT({data.longitude} {data.latitude})",
            srid=4326,
        )

        listing = Listing(
            title=data.title,
            district=data.district,
            monthly_rent=data.monthly_rent,
            bedrooms=data.bedrooms,
            area_sqm=data.area_sqm,
            floor=data.floor,
            orientation=data.orientation,
            pets_allowed=data.pets_allowed,
            near_main_road=data.near_main_road,
            available_date=data.available_date,
            subway_distance_m=data.subway_distance_m,
            description=data.description,
            location=location,
            area=data.area,
        )

        session.add(listing)

        # flush 将 INSERT 发送到数据库，但不会提交事务。
        await session.flush()

        # 重新读取数据库值，包括服务端默认值和空间字段。
        await session.refresh(listing)

        return listing

    async def get_by_id(
        self,
        session: AsyncSession,
        listing_id: UUID,
    ) -> Listing | None:
        """根据主键查询房源。"""
        return await session.get(Listing, listing_id)

    async def get_by_ids(
        self,
        session: AsyncSession,
        listing_ids: list[UUID],
    ) -> list[Listing]:
        """使用一次 SQL 查询批量读取房源。

        Repository 不负责恢复调用方输入顺序，
        因为 SQL 的 IN 查询本身不保证返回顺序。
        顺序恢复和缺失房源判断属于 Service 的业务职责。
        """

        if not listing_ids:
            return []

        statement = select(Listing).where(
            Listing.id.in_(listing_ids),
        )

        result = await session.execute(statement)

        return list(result.scalars().all())

    async def search(
        self,
        session: AsyncSession,
        params: ListingSearchParams,
    ) -> tuple[list[tuple[Listing, float | None]], int]:
        """根据硬性条件筛选可租房源并返回总数。"""

        # 默认只向租客展示可租状态的房源。
        conditions = [Listing.status == "available"]

        if params.max_rent is not None:
            conditions.append(Listing.monthly_rent <= params.max_rent)

        if params.bedrooms is not None:
            conditions.append(Listing.bedrooms == params.bedrooms)

        if params.pets_allowed is not None:
            conditions.append(Listing.pets_allowed == params.pets_allowed)

        if params.available_before is not None:
            conditions.append(Listing.available_date <= params.available_before)

        if params.district is not None:
            conditions.append(Listing.district == params.district)

        if params.area is not None:
            conditions.append(Listing.area == params.area)

        # 没有位置参数时，距离列统一返回 NULL。
        distance_expression = cast(
            ColumnElement[float | None],
            sql_cast(literal(None), Float),
        )

        if (
            params.longitude is not None
            and params.latitude is not None
            and params.radius_m is not None
        ):
            # ST_MakePoint 的参数顺序为经度、纬度。
            reference_point = cast(
                ColumnElement[WKBElement],
                sql_cast(
                    func.ST_SetSRID(
                        func.ST_MakePoint(
                            params.longitude,
                            params.latitude,
                        ),
                        4326,
                    ),
                    Geography(
                        geometry_type="POINT",
                        srid=4326,
                    ),
                ),
            )

            # Geography 类型下，ST_DWithin 的距离单位是米。
            conditions.append(
                cast(
                    ColumnElement[bool],
                    func.ST_DWithin(
                        Listing.location,
                        reference_point,
                        params.radius_m,
                    ),
                )
            )

            distance_expression = cast(
                ColumnElement[float | None],
                sql_cast(
                    func.ST_Distance(
                        Listing.location,
                        reference_point,
                    ),
                    Float,
                ),
            )

        # 总数查询不受 limit 和 offset 影响，供前端计算分页。
        count_statement = select(func.count()).select_from(Listing).where(*conditions)
        total = await session.scalar(count_statement)

        # 添加 id 作为第二排序条件，保证相同租金下的分页顺序稳定。
        search_statement = select(
            Listing,
            distance_expression.label("distance_m"),
        ).where(*conditions)

        # 提供参考位置时优先按实际距离排序；
        # 否则保持原来的租金排序。
        if params.longitude is not None:
            search_statement = search_statement.order_by(
                distance_expression.asc(),
                Listing.monthly_rent.asc(),
                Listing.id.asc(),
            )
        else:
            search_statement = search_statement.order_by(
                Listing.monthly_rent.asc(),
                Listing.id.asc(),
            )

        search_statement = search_statement.limit(params.limit).offset(params.offset)

        result = await session.execute(search_statement)

        items = [
            (
                listing,
                float(distance) if distance is not None else None,
            )
            for listing, distance in result.tuples().all()
        ]

        return items, int(total or 0)
