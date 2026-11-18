"""Embedding 检索离线评测指标。"""

from collections.abc import Mapping, Sequence

from pydantic import BaseModel, Field

from app.modules.embeddings.evaluation import (
    EmbeddingEvaluationDataset,
)


class RetrievalMetrics(BaseModel):
    """一次检索评测的汇总结果。"""

    query_count: int = Field(gt=0)
    k: int = Field(gt=0)
    recall_at_k: float = Field(ge=0, le=1)
    mean_reciprocal_rank: float = Field(ge=0, le=1)


def evaluate_rankings(
    dataset: EmbeddingEvaluationDataset,
    rankings: Mapping[str, Sequence[str]],
    *,
    k: int,
) -> RetrievalMetrics:
    """根据每条查询的文档排名计算 Recall@K 和 MRR。

    rankings 的 key 是 query ID；
    value 是按相似度从高到低排列的文档 ID。
    """

    if k <= 0:
        raise ValueError("k must be positive")

    known_document_ids = {document.id for document in dataset.documents}
    expected_query_ids = {query.id for query in dataset.queries}
    missing_query_ids = expected_query_ids - set(rankings)

    if missing_query_ids:
        missing_text = ", ".join(sorted(missing_query_ids))
        raise ValueError(f"rankings are missing queries: {missing_text}")

    recall_total = 0.0
    reciprocal_rank_total = 0.0

    for query in dataset.queries:
        ranked_document_ids = list(
            rankings[query.id],
        )

        if len(ranked_document_ids) != len(set(ranked_document_ids)):
            raise ValueError(f"ranking for {query.id} contains duplicate documents")

        unknown_document_ids = set(ranked_document_ids) - known_document_ids

        if unknown_document_ids:
            unknown_text = ", ".join(sorted(unknown_document_ids))
            raise ValueError(f"ranking for {query.id} contains unknown documents: {unknown_text}")

        relevant_document_ids = set(
            query.relevant_document_ids,
        )
        top_k_document_ids = set(
            ranked_document_ids[:k],
        )

        recall_total += len(relevant_document_ids & top_k_document_ids) / len(relevant_document_ids)

        first_relevant_rank = next(
            (
                rank
                for rank, document_id in enumerate(
                    ranked_document_ids,
                    start=1,
                )
                if document_id in relevant_document_ids
            ),
            None,
        )

        if first_relevant_rank is not None:
            reciprocal_rank_total += 1 / first_relevant_rank

    query_count = len(dataset.queries)

    return RetrievalMetrics(
        query_count=query_count,
        k=k,
        recall_at_k=recall_total / query_count,
        mean_reciprocal_rank=(reciprocal_rank_total / query_count),
    )
