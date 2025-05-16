from pydantic import BaseModel, Field
from typing import Optional, List
import datetime 
from decimal import Decimal

class CategoryBare(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2) 
    category_id: int
    sku: Optional[str] = Field(None, max_length=100)
    initial_quantity: int = Field(0, ge=0) 
    low_stock_threshold: Optional[int] = Field(10, ge=0)

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    category_id: Optional[int] = None
    sku: Optional[str] = Field(None, max_length=100)

class ProductBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    sku: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) 
        }

class Product(ProductBase):
    category: CategoryBare 

class ProductMinimal(BaseModel):
    id: int
    name: str
    price: Decimal
    sku: Optional[str] = None
    category_name: Optional[str] = None 

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        } 