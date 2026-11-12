"""生成符合基本业务规律的合成房源数据。

运行方式：
    python -m scripts.seed_listings
    python -m scripts.seed_listings --count 500 --seed 2026

同一个 seed 和序号会生成固定 UUID，因此脚本重复执行不会重复插入数据。
"""

import argparse
import asyncio
import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from app.db.session import async_session_factory
from app.modules.listings.models import Listing


@dataclass(frozen=True)
class DistrictProfile:
    """区域数据生成规则。"""

    name: str
    longitude: float
    latitude: float
    base_rent: int


DISTRICTS = (
    DistrictProfile("张江", 121.606, 31.204, 2_500),
    DistrictProfile("金桥", 121.602, 31.257, 2_200),
    DistrictProfile("唐镇", 121.657, 31.214, 1_800),
    DistrictProfile("北蔡", 121.558, 31.180, 2_300),
    DistrictProfile("川沙", 121.699, 31.186, 1_600),
)

ORIENTATIONS = ("南", "东南", "东", "西", "北")
BEDROOM_WEIGHTS = (0, 1, 1, 1, 2, 2, 3)

AREA_RANGES = {
    0: (25.0, 40.0),
    1: (38.0, 65.0),
    2: (65.0, 95.0),
    3: (90.0, 130.0),
}


def generate_listing(
    rng: random.Random,
    index: int,
    seed: int,
) -> Listing:
    """按照约束关系生成一套房源。"""

    district = rng.choice(DISTRICTS)
    bedrooms = rng.choice(BEDROOM_WEIGHTS)
    orientation = rng.choice(ORIENTATIONS)

    min_area, max_area = AREA_RANGES[bedrooms]
    area = round(rng.uniform(min_area, max_area), 2)

    subway_distance = rng.randint(150, 2_500)
    pets_allowed = rng.random() < 0.4
    near_main_road = rng.random() < 0.25

    # 在区域中心附近约几公里范围内生成坐标。
    longitude = round(
        district.longitude + rng.uniform(-0.03, 0.03),
        6,
    )
    latitude = round(
        district.latitude + rng.uniform(-0.03, 0.03),
        6,
    )

    # 租金由区域、面积、户型、地铁距离和随机扰动共同决定。
    raw_rent = (
        district.base_rent
        + area * 38
        + bedrooms * 250
        - subway_distance * 0.15
        + rng.randint(-300, 300)
    )
    monthly_rent = max(
        1_500,
        round(raw_rent / 100) * 100,
    )

    if bedrooms == 0:
        room_name = "开间"
    else:
        room_name = f"{bedrooms}室1厅"

    noise_description = "靠近主干道，出行方便" if near_main_road else "位于小区内部，相对安静"
    pet_description = "允许饲养宠物" if pets_allowed else "暂不允许饲养宠物"

    description = (
        f"{district.name}{orientation}向{room_name}，"
        f"{noise_description}，"
        f"距离地铁约{subway_distance}米，"
        f"{pet_description}。"
    )

    # UUID 由 seed 和序号确定，保证重复运行时身份稳定。
    listing_id = uuid5(
        NAMESPACE_URL,
        f"rentflow-listing-{seed}-{index}",
    )

    return Listing(
        id=listing_id,
        title=f"{district.name}{orientation}向{room_name}-{index + 1:03d}",
        district=district.name,
        monthly_rent=monthly_rent,
        bedrooms=bedrooms,
        area_sqm=Decimal(str(area)),
        floor=rng.randint(1, 30),
        orientation=orientation,
        pets_allowed=pets_allowed,
        near_main_road=near_main_road,
        available_date=date.today() + timedelta(days=rng.randint(0, 60)),
        subway_distance_m=subway_distance,
        description=description,
        location=WKTElement(
            f"POINT({longitude} {latitude})",
            srid=4326,
        ),
        status="available",
    )


async def seed_listings(count: int, seed: int) -> None:
    """生成房源并跳过数据库中已经存在的确定性 UUID。"""

    rng = random.Random(seed)

    generated_listings = [generate_listing(rng, index, seed) for index in range(count)]
    generated_ids: list[UUID] = [listing.id for listing in generated_listings]

    async with async_session_factory() as session:
        existing_result = await session.scalars(
            select(Listing.id).where(Listing.id.in_(generated_ids))
        )
        existing_ids = set(existing_result.all())

        new_listings = [listing for listing in generated_listings if listing.id not in existing_ids]

        try:
            session.add_all(new_listings)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    print(f"Generated: {count}, inserted: {len(new_listings)}, skipped: {len(existing_ids)}")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="Generate synthetic rental listings.")
    parser.add_argument(
        "--count",
        type=int,
        default=300,
        help="Number of listings to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2026,
        help="Random seed used for reproducibility.",
    )

    args = parser.parse_args()

    if args.count <= 0:
        parser.error("--count must be greater than 0")

    return args


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    asyncio.run(seed_listings(args.count, args.seed))


if __name__ == "__main__":
    main()
