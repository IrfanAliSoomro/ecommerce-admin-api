from pydantic import BaseModel, Field
from typing import Optional
import datetime
from .product import ProductMinimal 

class InventoryUpdate(BaseModel):
    quantity_change: Optional[int] = None 
    absolute_quantity: Optional[int] = Field(None, ge=0) 
    reason: Optional[str] = Field(None, max_length=255)
    low_stock_threshold: Optional[int] = Field(None, ge=0)

class InventoryBase(BaseModel):
    quantity: int
    low_stock_threshold: int
    last_updated: datetime.datetime

    class Config:
        from_attributes = True

class Inventory(InventoryBase):
    id: int
    product_id: int
    product: ProductMinimal 
    is_low_stock: Optional[bool] = None 

class InventoryLogCreate(BaseModel):
    product_id: int
    change_quantity: int
    new_quantity: int
    reason: Optional[str] = None

class InventoryLog(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None 
    change_quantity: int
    new_quantity: int
    reason: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True 