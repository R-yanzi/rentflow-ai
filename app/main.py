"""RentFlow AI 的 FastAPI 应用入口。"""

from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.request_id import RequestIdMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """根据配置创建 FastAPI 应用。

    如果传入了 Settings，则使用 FastAPI 的依赖覆盖机制，
    确保路由和应用元数据使用同一个配置对象。
    """
    application_settings = settings or get_settings()

    application = FastAPI(
        title=application_settings.name,
        description=application_settings.description,
        version=application_settings.version,
        debug=application_settings.debug,
    )

    if settings is not None:
        # 保存已完成类型收窄的配置对象，供依赖覆盖函数返回。
        provided_settings = settings

        def override_settings() -> Settings:
            """在测试或自定义应用实例中返回指定配置。"""
            return provided_settings

        # 所有 Depends(get_settings) 都会改为调用 override_settings。
        application.dependency_overrides[get_settings] = override_settings

    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)

    application.include_router(
        api_router,
        prefix=application_settings.api_v1_prefix,
    )

    return application


app = create_app()
