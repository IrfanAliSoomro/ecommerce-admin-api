from pydantic import BaseModel
from typing import Optional, List

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True 

class Category(CategoryBase):
    pass 

class ProductInCagetory(BaseModel): 
    id: int
    name: str
    price: float
    sku: Optional[str] = None
    class Config:
        from_attributes = True

class CategoryWithProducts(CategoryBase):
    products: List[ProductInCagetory] = [] 