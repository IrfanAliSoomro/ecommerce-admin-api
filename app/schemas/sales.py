from pydantic import BaseModel, Field
from typing import List, Optional, Union
import datetime
from decimal import Decimal

class SaleItemDetail(BaseModel):
    order_id: int
    order_date: datetime.datetime
    product_id: int
    product_name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    quantity_sold: int
    price_at_sale: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class SalesDataResponse(BaseModel):
    total_items: int
    items: List[SaleItemDetail]
    page: int
    page_size: int
    num_pages: int

class RevenueDataPoint(BaseModel):
    period_start: Union[datetime.date, datetime.datetime, str] 
    period_end: Union[datetime.date, datetime.datetime, str]  
    total_revenue: Decimal
    category_name: Optional[str] = None 

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class RevenueSummaryResponse(BaseModel):
    data: List[RevenueDataPoint]
    overall_total_revenue: Optional[Decimal] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class RevenueComparisonResponse(BaseModel):
    period1_start_date: datetime.date
    period1_end_date: datetime.date
    period1_revenue: Decimal
    period1_category_name: Optional[str] = None

    period2_start_date: datetime.date
    period2_end_date: datetime.date
    period2_revenue: Decimal
    period2_category_name: Optional[str] = None

    difference: Decimal
    percentage_change: float

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        } 