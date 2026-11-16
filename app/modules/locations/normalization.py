"""地点文本标准化工具。"""

import re
import unicodedata

# 这些字符在用户输入中通常只起分隔作用，
# 不应该影响地点名称匹配。
_LOCATION_SEPARATOR_PATTERN = re.compile(
    r"[\s·•・.,，。_\-—]+",
)


def normalize_location_text(value: str) -> str:
    """将地点文本转换为适合确定性匹配的形式。

    处理规则：
    1. 使用 NFKC 统一全角和半角字符；
    2. 使用 casefold 统一英文大小写；
    3. 删除空白和常见分隔符；
    4. 不擅自删除“地铁站”“园区”等具有业务含义的后缀。

    返回空字符串表示输入标准化后没有有效内容。
    """

    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.casefold()
    normalized = _LOCATION_SEPARATOR_PATTERN.sub("", normalized)

    return normalized