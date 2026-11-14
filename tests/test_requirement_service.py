"""自然语言租房需求提取服务测试。"""

import asyncio
from typing import TypeVar

from pydantic import BaseModel

from app.modules.search.schemas import RentalRequirements
from app.modules.search.service import RentalRequirementService

StructuredModel = TypeVar(
    "StructuredModel",
    bound=BaseModel,
)


class StubLLMProvider:
    """测试专用 Provider，不调用真实模型。"""

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[StructuredModel],
    ) -> StructuredModel:
        """返回预先定义的数据，并交给 Pydantic 校验."""

        assert system_prompt
        assert user_prompt == (
            "预算5000，在张江上班，通勤不超过40分钟，需要一室一厅，可以养猫，最好安静。"
        )

        return response_model.model_validate(
            {
                "district": None,
                "area": None,
                "max_rent": 5000,
                "bedrooms": 1,
                "pets_allowed": True,
                "available_before": None,
                "work_location": "张江",
                "max_commute_minutes": 40,
                "preferences": ["安静"],
            }
        )


def test_extract_rental_requirements() -> None:
    """业务服务应返回经过校验的结构化需求."""

    service = RentalRequirementService(StubLLMProvider())

    requirements = asyncio.run(
        service.extract(
            "预算5000，在张江上班，通勤不超过40分钟，需要一室一厅，可以养猫，最好安静。"
        )
    )

    assert isinstance(requirements, RentalRequirements)
    assert requirements.max_rent == 5000
    assert requirements.work_location == "张江"
    assert requirements.bedrooms == 1
    assert requirements.pets_allowed is True
    assert requirements.preferences == ["安静"]
