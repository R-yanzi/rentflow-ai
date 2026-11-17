"""通勤缓存请求指纹生成。"""

from hashlib import sha256
from uuid import UUID

from app.providers.commute.base import CommuteRequest

# 如果以后修改指纹字段或序列化规则，应提升版本号，
# 让新旧缓存自然隔离，避免错误复用。
FINGERPRINT_VERSION = "v1"

# WGS84 坐标保留 6 位小数，大约对应 0.1 米级精度。
# 这足够区分房源位置，也能避免浮点序列化噪声影响缓存命中。
COORDINATE_DECIMAL_PLACES = 6


def normalize_coordinate(value: float) -> str:
    """把浮点坐标转换为稳定的定长字符串。

    例如 121.6 和 121.600000 会统一表示为 121.600000。
    """

    return f"{value:.{COORDINATE_DECIMAL_PLACES}f}"


def build_commute_fingerprint(
    *,
    listing_id: UUID,
    destination_location_id: UUID,
    request: CommuteRequest,
    provider: str,
) -> str:
    """为一次通勤计算生成稳定的 SHA-256 指纹。

    指纹包含业务实体、实际坐标、交通方式、Provider 和指纹版本。
    因此房源位置、目的地位置、交通方式或算法版本发生变化时，
    都不会错误命中旧缓存。
    """

    fingerprint_parts = (
        FINGERPRINT_VERSION,
        str(listing_id),
        str(destination_location_id),
        normalize_coordinate(request.origin.longitude),
        normalize_coordinate(request.origin.latitude),
        normalize_coordinate(request.destination.longitude),
        normalize_coordinate(request.destination.latitude),
        request.mode.value,
        provider,
    )

    canonical_request = "|".join(fingerprint_parts)

    return sha256(
        canonical_request.encode("utf-8"),
    ).hexdigest()
