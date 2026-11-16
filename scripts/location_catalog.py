"""上海公共地点种子目录。

这些坐标用于 RentFlow AI 演示环境中的地点解析、地图展示和距离计算，
不作为导航、测绘或现实业务决策依据。
"""

from dataclasses import dataclass

from app.modules.locations.schemas import LocationType


@dataclass(frozen=True)
class LocationSeed:
    """一条可重复写入的标准地点数据。"""

    source_id: str
    canonical_name: str
    location_type: LocationType
    district: str
    area: str | None
    longitude: float
    latitude: float
    aliases: tuple[str, ...]


LOCATION_CATALOG = (
    LocationSeed(
        source_id="district-pudong",
        canonical_name="浦东新区",
        location_type="district",
        district="浦东新区",
        area=None,
        longitude=121.5447,
        latitude=31.2215,
        aliases=("浦东", "浦东区", "浦东新区"),
    ),
    LocationSeed(
        source_id="area-zhangjiang",
        canonical_name="张江板块",
        location_type="area",
        district="浦东新区",
        area="张江",
        longitude=121.6060,
        latitude=31.2040,
        aliases=("张江", "张江板块"),
    ),
    LocationSeed(
        source_id="area-jinqiao",
        canonical_name="金桥板块",
        location_type="area",
        district="浦东新区",
        area="金桥",
        longitude=121.6020,
        latitude=31.2570,
        aliases=("金桥", "金桥板块"),
    ),
    LocationSeed(
        source_id="area-tangzhen",
        canonical_name="唐镇板块",
        location_type="area",
        district="浦东新区",
        area="唐镇",
        longitude=121.6570,
        latitude=31.2140,
        aliases=("唐镇", "唐镇板块"),
    ),
    LocationSeed(
        source_id="area-beicai",
        canonical_name="北蔡板块",
        location_type="area",
        district="浦东新区",
        area="北蔡",
        longitude=121.5580,
        latitude=31.1800,
        aliases=("北蔡", "北蔡板块"),
    ),
    LocationSeed(
        source_id="area-chuansha",
        canonical_name="川沙板块",
        location_type="area",
        district="浦东新区",
        area="川沙",
        longitude=121.6990,
        latitude=31.1860,
        aliases=("川沙", "川沙板块"),
    ),
    LocationSeed(
        source_id="metro-zhangjiang-gaoke",
        canonical_name="张江高科地铁站",
        location_type="metro_station",
        district="浦东新区",
        area="张江",
        longitude=121.5877,
        latitude=31.2018,
        aliases=("张江高科站", "张江高科地铁站"),
    ),
    LocationSeed(
        source_id="metro-jinke-road",
        canonical_name="金科路地铁站",
        location_type="metro_station",
        district="浦东新区",
        area="张江",
        longitude=121.6020,
        latitude=31.2042,
        aliases=("金科路", "金科路站", "金科路地铁站"),
    ),
    LocationSeed(
        source_id="metro-guanglan-road",
        canonical_name="广兰路地铁站",
        location_type="metro_station",
        district="浦东新区",
        area="张江",
        longitude=121.6211,
        latitude=31.2111,
        aliases=("广兰路", "广兰路站", "广兰路地铁站"),
    ),
    LocationSeed(
        source_id="metro-tangzhen",
        canonical_name="唐镇地铁站",
        location_type="metro_station",
        district="浦东新区",
        area="唐镇",
        longitude=121.6569,
        latitude=31.2140,
        aliases=("唐镇站", "唐镇地铁站"),
    ),
    LocationSeed(
        source_id="metro-chuansha",
        canonical_name="川沙地铁站",
        location_type="metro_station",
        district="浦东新区",
        area="川沙",
        longitude=121.6982,
        latitude=31.1867,
        aliases=("川沙站", "川沙地铁站"),
    ),
    LocationSeed(
        source_id="office-zhangjiang-science-city",
        canonical_name="张江科学城",
        location_type="office_area",
        district="浦东新区",
        area="张江",
        longitude=121.5995,
        latitude=31.2010,
        aliases=("张江", "张江科学城", "张江高科技园区"),
    ),
    LocationSeed(
        source_id="office-lujiazui",
        canonical_name="陆家嘴金融城",
        location_type="office_area",
        district="浦东新区",
        area="陆家嘴",
        longitude=121.5023,
        latitude=31.2382,
        aliases=("陆家嘴", "陆家嘴金融城", "陆家嘴金融区"),
    ),
)