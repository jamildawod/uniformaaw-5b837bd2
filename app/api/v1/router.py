from fastapi import APIRouter

from app.api.admin_intelligence import router as admin_intelligence_router
from app.api.v1.endpoints.admin_pim import router as admin_pim_router
from app.api.v1.endpoints.admin_extended import router as admin_extended_router
from app.api.v1.endpoints.admin_products import router as admin_products_router
from app.api.v1.endpoints.admin_super_deals import router as admin_super_deals_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.public_products import router as public_products_router
from app.api.v1.endpoints.public_super_deals import router as public_super_deals_router
from app.api.v1.endpoints.categories import router as categories_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(public_products_router, tags=["products"])
api_router.include_router(public_super_deals_router, tags=["super-deals"])
api_router.include_router(admin_products_router, tags=["admin-products"])
api_router.include_router(admin_super_deals_router, tags=["admin-super-deals"])
api_router.include_router(admin_pim_router, tags=["admin-pim"])
api_router.include_router(admin_extended_router, tags=["admin"])
api_router.include_router(admin_intelligence_router, tags=["admin-intelligence"])
api_router.include_router(categories_router, tags=["categories"])
