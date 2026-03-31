from fastapi import APIRouter, Depends
from app.core.deps import get_current_admin

router = APIRouter()

SUPER_DEALS = []

@router.get("/super-deals")
def get_super_deals():
    return SUPER_DEALS

@router.post("/admin/super-deals")
def save_super_deals(payload: dict, admin=Depends(get_current_admin)):
    global SUPER_DEALS
    SUPER_DEALS = payload.get("product_ids", [])
    return {"success": True, "items": SUPER_DEALS}
