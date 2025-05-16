from fastapi import APIRouter

# Import endpoint modules here once they are created
from .endpoints import products, categories, inventory, orders, sales_reports

router = APIRouter()

# Include routers from endpoint modules
router.include_router(categories.router, prefix="/categories", tags=["Categories"])
router.include_router(products.router, prefix="/products", tags=["Products"])
router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
router.include_router(orders.router, prefix="/orders", tags=["Orders"])
router.include_router(sales_reports.router, prefix="/reports", tags=["Sales & Revenue Reports"])

# A health check or root for this v1 router could also be added here if desired
# @router.get("/", tags=["API V1 Root"])
# def read_v1_root():
#     return {"message": "API V1 is active"} 