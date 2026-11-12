"""自然语言房源搜索 API。"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.listings.dependencies import get_listing_service
from app.modules.listings.service import ListingService
from app.modules.search.schemas import (
    NaturalLanguageSearchResponse,
    RentalRequirements,
    RequirementParseRequest,
)
from app.modules.search.service import (
    NaturalLanguageListingSearchService,
    RentalRequirementService,
)
from app.providers.llm.base import LLMProvider
from app.providers.llm.dependencies import get_llm_provider

router = APIRouter(prefix="/search", tags=["Search"])

LLMProviderDependency = Annotated[
    LLMProvider,
    Depends(get_llm_provider),
]

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]

ListingServiceDependency = Annotated[
    ListingService,
    Depends(get_listing_service),
]


@router.post(
    "/requirements",
    response_model=RentalRequirements,
    summary="解析自然语言租房需求",
)
async def parse_rental_requirements(
    request: RequirementParseRequest,
    provider: LLMProviderDependency,
) -> RentalRequirements:
    """使用 DeepSeek 将自然语言转换成结构化条件。"""

    service = RentalRequirementService(provider)
    return await service.extract(request.text)


@router.post(
    "/listings",
    response_model=NaturalLanguageSearchResponse,
    summary="使用自然语言搜索房源",
)
async def natural_language_listing_search(
    request: RequirementParseRequest,
    provider: LLMProviderDependency,
    session: DatabaseSession,
    listing_service: ListingServiceDependency,
) -> NaturalLanguageSearchResponse:
    """解析用户需求并执行确定性房源查询。"""

    requirement_service = RentalRequirementService(provider)

    search_service = NaturalLanguageListingSearchService(
        requirement_service=requirement_service,
        listing_service=listing_service,
    )
    return await search_service.search(
        session=session,
        user_text=request.text,
    )
