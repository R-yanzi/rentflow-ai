"""自然语言租房需求提取与搜索编排服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.schemas import ListingSearchParams
from app.modules.listings.service import ListingService
from app.modules.search.prompts import RENTAL_REQUIREMENT_SYSTEM_PROMPT
from app.modules.search.schemas import (
    NaturalLanguageSearchResponse,
    RentalRequirements,
)
from app.providers.llm.base import LLMProvider


class RentalRequirementService:
    """协调业务 Prompt 与底层 LLM Provider。"""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def extract(
        self,
        user_text: str,
    ) -> RentalRequirements:
        """从用户自然语言中提取结构化租房条件。"""

        return await self._provider.generate_structured(
            system_prompt=RENTAL_REQUIREMENT_SYSTEM_PROMPT,
            user_prompt=user_text,
            response_model=RentalRequirements,
        )


def build_listing_search_params(
    requirements: RentalRequirements,
) -> ListingSearchParams:
    """将大模型输出映射成数据库能够执行的确定性条件。"""

    return ListingSearchParams(
        district=requirements.district,
        max_rent=requirements.max_rent,
        bedrooms=requirements.bedrooms,
        pets_allowed=requirements.pets_allowed,
        available_before=requirements.available_before,
        limit=20,
        offset=0,
    )


def collect_unresolved_requirements(
    requirements: RentalRequirements,
) -> list[str]:
    """收集当前阶段尚不能可靠执行的条件。"""

    unresolved: list[str] = []

    if requirements.work_location is not None:
        unresolved.append("work_location")

    if requirements.max_commute_minutes is not None:
        unresolved.append("max_commute_minutes")

    if requirements.preferences:
        unresolved.append("preferences")

    return unresolved


class NaturalLanguageListingSearchService:
    """编排需求提取与确定性房源查询。"""

    def __init__(
        self,
        requirement_service: RentalRequirementService,
        listing_service: ListingService,
    ) -> None:
        self._requirement_service = requirement_service
        self._listing_service = listing_service

    async def search(
        self,
        session: AsyncSession,
        user_text: str,
    ) -> NaturalLanguageSearchResponse:
        """解析需求并调用已有房源查询能力。"""

        requirements = await self._requirement_service.extract(user_text)
        search_params = build_listing_search_params(requirements)

        results = await self._listing_service.search(
            session,
            search_params,
        )

        return NaturalLanguageSearchResponse(
            requirements=requirements,
            results=results,
            unresolved_requirements=collect_unresolved_requirements(requirements),
        )
