"""自然语言房源搜索 API 闭环测试。"""

from typing import TypeVar

from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.modules.listings.dependencies import get_listing_service
from app.modules.listings.schemas import (
    ListingListResponse,
    ListingSearchParams,
)
from app.providers.llm.base import LLMProvider
from app.providers.llm.dependencies import get_llm_provider

StructuredModel = TypeVar(
    "StructuredModel",
    bound=BaseModel,
)


class StubLLMProvider:
    """不调用真实 DeepSeek 的测试 Provider。"""

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[StructuredModel],
    ) -> StructuredModel:
        assert system_prompt
        assert user_prompt

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


class StubListingService:
    """不连接数据库的测试房源服务。"""

    async def search(
        self,
        session: AsyncSession,
        params: ListingSearchParams,
    ) -> ListingListResponse:
        # 验证 LLM 结果确实被映射成了数据库查询参数。
        assert params.max_rent == 5000
        assert params.bedrooms == 1
        assert params.pets_allowed is True

        return ListingListResponse(
            items=[],
            total=0,
            limit=params.limit,
            offset=params.offset,
        )


def provide_stub_llm() -> LLMProvider:
    """提供测试 LLM。"""
    return StubLLMProvider()


def provide_stub_listing_service() -> StubListingService:
    """提供测试房源服务。"""
    return StubListingService()


def test_natural_language_search_pipeline() -> None:
    """自然语言应经过提取、映射并调用房源服务。"""

    application = create_app()
    application.dependency_overrides[get_llm_provider] = provide_stub_llm
    application.dependency_overrides[get_listing_service] = provide_stub_listing_service

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/search/listings",
            json={
                "text": (
                    "预算5000，在张江上班，通勤不超过40分钟，需要一室一厅，可以养猫，最好安静。"
                )
            },
        )

    body = response.json()

    assert response.status_code == 200
    assert body["requirements"]["max_rent"] == 5000
    assert body["requirements"]["work_location"] == "张江"
    assert body["results"]["total"] == 0
    assert body["unresolved_requirements"] == [
        "work_location",
        "max_commute_minutes",
        "preferences",
    ]
    assert response.headers["X-Request-ID"]


class FailIfCalledLLMProvider:
    """确认搜索中只要调用 LLM，测试就应该立即失败。"""

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[StructuredModel],
    ) -> StructuredModel:
        raise AssertionError("Confirmed search must not call the LLM")


def provide_failing_llm() -> LLMProvider:
    """提供一个禁止调用的 LLM Provider。"""
    return FailIfCalledLLMProvider()


def test_confirmed_requirement_search_does_not_call_llm() -> None:
    """用户确认后的条件应该直接进入确定性搜索。"""

    application = create_app()

    # 如果接口错误地再次调用 LLM，FailIfCalledLLMProvider 会使测试失败。
    application.dependency_overrides[get_llm_provider] = provide_failing_llm
    application.dependency_overrides[get_listing_service] = provide_stub_listing_service

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/search/listings/confirmed",
            json={
                "district": None,
                "area": None,
                "max_rent": 5000,
                "bedrooms": 1,
                "pets_allowed": True,
                "available_before": None,
                "work_location": "张江",
                "max_commute_minutes": 40,
                "preferences": ["安静"],
            },
        )

    body = response.json()

    assert response.status_code == 200
    assert body["requirements"]["max_rent"] == 5000
    assert body["results"]["total"] == 0
    assert body["unresolved_requirements"] == [
        "work_location",
        "max_commute_minutes",
        "preferences",
    ]
