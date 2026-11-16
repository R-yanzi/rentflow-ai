"""地点文本标准化测试。"""

from app.modules.locations.normalization import normalize_location_text


def test_normalize_location_text_unifies_width_case_and_whitespace() -> None:
    """全角字符、英文大小写和空白不应影响匹配。"""

    result = normalize_location_text(
        "  ＺＨＡＮＧ　ＪＩＡＮＧ  ",
    )

    assert result == "zhangjiang"


def test_normalize_location_text_removes_common_separators() -> None:
    """常见分隔符不应影响地点名称匹配。"""

    assert normalize_location_text("张江・高科") == "张江高科"
    assert normalize_location_text("张江-高科") == "张江高科"


def test_normalize_location_text_preserves_semantic_suffixes() -> None:
    """地点类型相关后缀必须保留，不能被字符串规则误删。"""

    assert normalize_location_text("张江高科地铁站") == "张江高科地铁站"


def test_normalize_location_text_returns_empty_for_blank_input() -> None:
    """只有空白或分隔符的输入应该得到空字符串。"""

    assert normalize_location_text("  · - ，  ") == ""