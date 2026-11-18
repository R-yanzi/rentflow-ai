"""Embedding 检索评测集模型。"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvaluationDocument(BaseModel):
    """一条用于检索评测的合成房源文本。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1)
    traits: list[str] = Field(
        min_length=1,
        description="该文本明确表达的软偏好标签",
    )


class EvaluationQuery(BaseModel):
    """一条用户软偏好查询及其相关文档。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1)
    relevant_document_ids: list[str] = Field(
        min_length=1,
    )


class EmbeddingEvaluationDataset(BaseModel):
    """完整的软偏好语义检索评测集。"""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    documents: list[EvaluationDocument] = Field(
        min_length=2,
    )
    queries: list[EvaluationQuery] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_dataset_references(self) -> Self:
        """保证 ID 唯一，并且相关性标注都指向真实文档。"""

        document_ids = [document.id for document in self.documents]
        query_ids = [query.id for query in self.queries]

        if len(document_ids) != len(set(document_ids)):
            raise ValueError("document IDs must be unique")

        if len(query_ids) != len(set(query_ids)):
            raise ValueError("query IDs must be unique")

        known_document_ids = set(document_ids)

        for query in self.queries:
            unknown_ids = set(query.relevant_document_ids) - known_document_ids

            if unknown_ids:
                unknown_text = ", ".join(sorted(unknown_ids))
                raise ValueError(f"query {query.id} references unknown documents: {unknown_text}")

        return self
