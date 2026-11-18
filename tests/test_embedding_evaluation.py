"""Embedding 软偏好评测集测试。"""

import json
from pathlib import Path
from typing import Any, cast

from app.modules.embeddings.evaluation import (
    EmbeddingEvaluationDataset,
)

DATASET_PATH = Path(__file__).parents[1] / "evals" / "soft_preference_retrieval.json"


def load_dataset() -> EmbeddingEvaluationDataset:
    """读取并验证仓库中的评测集。"""

    raw_data = cast(
        dict[str, Any],
        json.loads(
            DATASET_PATH.read_text(
                encoding="utf-8",
            )
        ),
    )

    return EmbeddingEvaluationDataset.model_validate(
        raw_data,
    )


def test_soft_preference_dataset_is_valid() -> None:
    """评测集应满足 Schema、唯一性和引用完整性。"""

    dataset = load_dataset()

    assert dataset.version == "soft-preference-v1"
    assert len(dataset.documents) == 8
    assert len(dataset.queries) == 6


def test_every_query_has_positive_and_negative_documents() -> None:
    """每条查询都必须同时存在相关和不相关文档。"""

    dataset = load_dataset()
    all_document_ids = {document.id for document in dataset.documents}

    for query in dataset.queries:
        relevant_ids = set(
            query.relevant_document_ids,
        )

        assert relevant_ids
        assert relevant_ids < all_document_ids


def test_core_soft_preferences_are_covered() -> None:
    """第一版至少覆盖项目需求中的核心软偏好。"""

    dataset = load_dataset()
    covered_traits = {trait for document in dataset.documents for trait in document.traits}

    assert {
        "安静",
        "采光好",
        "适合独居",
        "宠物友好",
    } <= covered_traits
