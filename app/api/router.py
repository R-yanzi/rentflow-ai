"""应用 API 路由汇总入口。"""

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.modules.commutes.router import router as commutes_router
from app.modules.listings.router import router as listings_router
from app.modules.locations.router import router as locations_router
from app.modules.search.router import router as search_router

api_router = APIRouter()
api_router.include_router(commutes_router)
api_router.include_router(health_router)
api_router.include_router(listings_router)
api_router.include_router(locations_router)
api_router.include_router(search_router)
