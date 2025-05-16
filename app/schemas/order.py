from pydantic import BaseModel, Field
from typing import List, Optional
import datetime
from decimal import Decimal
from .product import ProductMinimal 

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_name: Optional[str] = Field(None, max_length=255)
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderItem(BaseModel): 
    id: int
    product_id: int
    quantity: int
    price_at_sale: Decimal
    subtotal: Decimal
    product: Optional[ProductMinimal] = None 

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class OrderBase(BaseModel):
    id: int
    order_date: datetime.datetime
    customer_name: Optional[str] = None
    status: str
    total_amount: Decimal

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class Order(OrderBase):
    item_count: Optional[int] = None 

class OrderDetails(OrderBase):
    items: List[OrderItem] = []

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    customer_name: Optional[str] = Field(None, max_length=255)
  