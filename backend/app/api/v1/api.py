from fastapi import APIRouter

from app.api.v1.endpoints import admin_super_deals

api_router = APIRouter()

api_router.include_router(admin_super_deals.router, prefix="/api/v1")
