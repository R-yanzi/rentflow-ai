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
    *,
    limit: int = 20,
    offset: int = 0,
) -> ListingSearchParams:
    """把已确认需求映射为数据库能够执行的确定性查询条件。"""

    return ListingSearchParams(
        district=requirements.district,
        area=requirements.area,
        max_rent=requirements.max_rent,
        bedrooms=requirements.bedrooms,
        pets_allowed=requirements.pets_allowed,
        available_before=requirements.available_before,
        limit=limit,
        offset=offset,
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


async def search_confirmed_requirements(
    *,
    session: AsyncSession,
    listing_service: ListingService,
    requirements: RentalRequirements,
    limit: int = 20,
    offset: int = 0,
) -> NaturalLanguageSearchResponse:
    """使用用户确认后的条件执行确定性、可分页的房源搜索。"""

    search_params = build_listing_search_params(
        requirements,
        limit=limit,
        offset=offset,
    )

    results = await listing_service.search(
        session,
        search_params,
    )

    return NaturalLanguageSearchResponse(
        requirements=requirements,
        results=results,
        unresolved_requirements=collect_unresolved_requirements(requirements),
    )


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
        """解析自然语言，然后执行确定性房源查询。"""

        requirements = await self._requirement_service.extract(user_text)

        return await search_confirmed_requirements(
            session=session,
            listing_service=self._listing_service,
            requirements=requirements,
        )
