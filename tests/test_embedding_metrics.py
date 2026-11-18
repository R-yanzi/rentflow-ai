"""Embedding 检索指标测试。"""

import pytest

from app.modules.embeddings.evaluation import (
    EmbeddingEvaluationDataset,
    EvaluationDocument,
    EvaluationQuery,
)
from app.modules.embeddings.metrics import (
    evaluate_rankings,
)


def create_dataset() -> EmbeddingEvaluationDataset:
    """构造容易人工验证指标的最小数据集。"""

    return EmbeddingEvaluationDataset(
        version="test-v1",
        documents=[
            EvaluationDocument(
                id="d1",
                text="安静房源",
                traits=["安静"],
            ),
            EvaluationDocument(
                id="d2",
                text="采光房源",
                traits=["采光好"],
            ),
            EvaluationDocument(
                id="d3",
                text="热闹房源",
                traits=["热闹"],
            ),
        ],
        queries=[
            EvaluationQuery(
                id="q1",
                text="晚上不要太吵",
                relevant_document_ids=["d1"],
            ),
            EvaluationQuery(
                id="q2",
                text="阳光充足",
                relevant_document_ids=["d2"],
            ),
        ],
    )


def test_evaluate_rankings_calculates_recall_and_mrr() -> None:
    """验证 Recall@1 和 MRR 的人工可计算结果。"""

    metrics = evaluate_rankings(
        create_dataset(),
        {
            "q1": ["d1", "d3", "d2"],
            "q2": ["d3", "d2", "d1"],
        },
        k=1,
    )

    # q1 的相关文档排第 1，q2 排第 2。
    # Recall@1 = (1 + 0) / 2 = 0.5
    # MRR = (1 + 1/2) / 2 = 0.75
    assert metrics.query_count == 2
    assert metrics.k == 1
    assert metrics.recall_at_k == pytest.approx(0.5)
    assert metrics.mean_reciprocal_rank == pytest.approx(0.75)


def test_recall_at_two_finds_both_relevant_documents() -> None:
    """当相关文档都进入前两名时 Recall@2 应为 1。"""

    metrics = evaluate_rankings(
        create_dataset(),
        {
            "q1": ["d1", "d3", "d2"],
            "q2": ["d3", "d2", "d1"],
        },
        k=2,
    )

    assert metrics.recall_at_k == pytest.approx(1.0)
    assert metrics.mean_reciprocal_rank == pytest.approx(0.75)


@pytest.mark.parametrize(
    ("rankings", "expected_message"),
    [
        (
            {
                "q1": ["d1", "d2", "d3"],
            },
            "rankings are missing queries",
        ),
        (
            {
                "q1": ["d1", "d1"],
                "q2": ["d2", "d3"],
            },
            "contains duplicate documents",
        ),
        (
            {
                "q1": ["unknown"],
                "q2": ["d2"],
            },
            "contains unknown documents",
        ),
    ],
)
def test_invalid_rankings_are_rejected(
    rankings: dict[str, list[str]],
    expected_message: str,
) -> None:
    """不完整或不可信的排名不能生成评测结果。"""

    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        evaluate_rankings(
            create_dataset(),
            rankings,
            k=1,
        )


def test_k_must_be_positive() -> None:
    """Recall@K 的 K 必须大于零。"""

    with pytest.raises(
        ValueError,
        match="k must be positive",
    ):
        evaluate_rankings(
            create_dataset(),
            {
                "q1": ["d1"],
                "q2": ["d2"],
            },
            k=0,
        )
