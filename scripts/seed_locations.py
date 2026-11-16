"""将上海公共地点目录同步到数据库。

运行方式：
    python -m scripts.seed_locations

脚本使用 source + source_id 识别同一个标准地点。
重复执行会更新现有地点和别名，不会重复插入。
"""

import asyncio
from uuid import NAMESPACE_URL, UUID, uuid5

from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.modules.locations.models import Location, LocationAlias
from app.modules.locations.normalization import normalize_location_text
from scripts.location_catalog import LOCATION_CATALOG, LocationSeed

LOCATION_SOURCE = "local_seed"


def location_id_for(source_id: str) -> UUID:
    """根据稳定来源编号生成可复现的地点 UUID。"""

    return uuid5(
        NAMESPACE_URL,
        f"rentflow-location-{LOCATION_SOURCE}-{source_id}",
    )


def alias_id_for(
    location_id: UUID,
    normalized_alias: str,
) -> UUID:
    """根据地点与标准化别名生成可复现的别名 UUID。"""

    return uuid5(
        NAMESPACE_URL,
        (
            "rentflow-location-alias-"
            f"{location_id}-{normalized_alias}"
        ),
    )


def build_point(seed: LocationSeed) -> WKBElement:
    """构造 SRID 4326 的 PostGIS 点。"""

    return from_shape(
        Point(seed.longitude, seed.latitude),
        srid=4326,
    )


def desired_aliases(
    seed: LocationSeed,
) -> dict[str, str]:
    """生成标准化别名到展示名称的映射。

    标准名称也必须参与精确匹配，因此即使目录没有显式把它
    写入 aliases，这里也会自动加入。
    """

    values = (
        seed.canonical_name,
        *seed.aliases,
    )

    result: dict[str, str] = {}

    for alias in values:
        normalized_alias = normalize_location_text(alias)

        if normalized_alias:
            result.setdefault(
                normalized_alias,
                alias,
            )

    return result


def build_location(seed: LocationSeed) -> Location:
    """根据目录数据创建新的 Location ORM 对象。"""

    location_id = location_id_for(seed.source_id)

    location = Location(
        id=location_id,
        canonical_name=seed.canonical_name,
        normalized_name=normalize_location_text(
            seed.canonical_name,
        ),
        location_type=seed.location_type,
        district=seed.district,
        area=seed.area,
        location=build_point(seed),
        source=LOCATION_SOURCE,
        source_id=seed.source_id,
        is_active=True,
    )

    location.aliases = [
        LocationAlias(
            id=alias_id_for(
                location_id,
                normalized_alias,
            ),
            location_id=location_id,
            alias=alias,
            normalized_alias=normalized_alias,
        )
        for normalized_alias, alias in desired_aliases(
            seed,
        ).items()
    ]

    return location


def synchronize_location(
    location: Location,
    seed: LocationSeed,
) -> None:
    """用目录内容更新已有地点和别名集合。"""

    location.canonical_name = seed.canonical_name
    location.normalized_name = normalize_location_text(
        seed.canonical_name,
    )
    location.location_type = seed.location_type
    location.district = seed.district
    location.area = seed.area
    location.location = build_point(seed)
    location.is_active = True

    existing_aliases = {
        alias.normalized_alias: alias
        for alias in location.aliases
    }

    synchronized_aliases: list[LocationAlias] = []

    for normalized_alias, alias_text in desired_aliases(
        seed,
    ).items():
        existing_alias = existing_aliases.get(
            normalized_alias,
        )

        if existing_alias is not None:
            existing_alias.alias = alias_text
            synchronized_aliases.append(existing_alias)
            continue

        synchronized_aliases.append(
            LocationAlias(
                id=alias_id_for(
                    location.id,
                    normalized_alias,
                ),
                location_id=location.id,
                alias=alias_text,
                normalized_alias=normalized_alias,
            )
        )

    # relationship 配置了 delete-orphan。
    # 不再出现在目录中的旧别名会在提交时被删除。
    location.aliases = synchronized_aliases


async def seed_locations() -> None:
    """将整个地点目录幂等同步到数据库。"""

    async with async_session_factory() as session:
        result = await session.execute(
            select(Location)
            .options(selectinload(Location.aliases))
            .where(
                Location.source == LOCATION_SOURCE,
            )
        )

        existing_locations = {
            location.source_id: location
            for location in result.scalars().unique().all()
        }

        inserted = 0
        updated = 0

        for seed in LOCATION_CATALOG:
            existing_location = existing_locations.get(
                seed.source_id,
            )

            if existing_location is None:
                session.add(
                    build_location(seed),
                )
                inserted += 1
            else:
                synchronize_location(
                    existing_location,
                    seed,
                )
                updated += 1

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    print(
        f"Locations synchronized: "
        f"inserted={inserted}, updated={updated}"
    )


def main() -> None:
    """脚本入口。"""

    asyncio.run(seed_locations())


if __name__ == "__main__":
    main()