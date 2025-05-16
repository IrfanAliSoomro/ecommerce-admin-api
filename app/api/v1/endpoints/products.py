from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import crud
from app.db.database import get_db
from app.schemas import product as product_schemas # Use the alias
from app.schemas import category as category_schemas # For validating category existence

router = APIRouter()

@router.post("/", response_model=product_schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: product_schemas.ProductCreate, 
    db: Session = Depends(get_db)
):
    """
    Register a new product.
    - **name**: Name of the product.
    - **description**: Optional detailed description.
    - **price**: Selling price of the product.
    - **category_id**: ID of the category this product belongs to.
    - **sku**: Optional Stock Keeping Unit (must be unique if provided).
    - **initial_quantity**: Initial stock quantity for this product.
    - **low_stock_threshold**: Optional threshold for low stock alerts.
    """
    # Validate category exists
    category = crud.get_category(db, category_id=product_in.category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category with ID {product_in.category_id} not found.")

    # Validate SKU uniqueness if provided
    if product_in.sku:
        existing_product_sku = crud.get_product_by_sku(db, sku=product_in.sku)
        if existing_product_sku:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product with SKU '{product_in.sku}' already exists.")
    
    # Potentially check for duplicate product name, though not strictly a DB constraint here
    # existing_product_name = db.query(models.Product).filter(func.lower(models.Product.name) == func.lower(product_in.name)).first()
    # if existing_product_name:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product with name '{product_in.name}' already exists.")

    return crud.create_product(db=db, product=product_in)

@router.get("/", response_model=List[product_schemas.Product])
def read_products(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"), 
    limit: int = Query(100, ge=0, le=200, description="Maximum number of records to return"), 
    category_id: Optional[int] = Query(None, description="Filter products by category ID"),
    name_contains: Optional[str] = Query(None, description="Filter products by name (case-insensitive, partial match)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of products with pagination and filtering options.
    """
    products = crud.get_products(db, skip=skip, limit=limit, category_id=category_id, name_contains=name_contains)
    return products

@router.get("/{product_id}", response_model=product_schemas.Product)
def read_product(
    product_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get a specific product by its ID.
    The response includes detailed information about the product, including its category.
    """
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return db_product

@router.put("/{product_id}", response_model=product_schemas.Product)
def update_product(
    product_id: int, 
    product_in: product_schemas.ProductUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update an existing product.
    Allows partial updates. Only fields present in the request body will be updated.
    Inventory quantity is managed via inventory endpoints, not here.
    """
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Validate category if category_id is being updated
    if product_in.category_id is not None and product_in.category_id != db_product.category_id:
        category = crud.get_category(db, category_id=product_in.category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category with ID {product_in.category_id} not found for update.")

    # Validate SKU uniqueness if SKU is being updated
    if product_in.sku and product_in.sku != db_product.sku:
        existing_product_sku = crud.get_product_by_sku(db, sku=product_in.sku)
        if existing_product_sku and existing_product_sku.id != product_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product with SKU '{product_in.sku}' already exists.")

    updated_product = crud.update_product(db=db, product_id=product_id, product_update=product_in)
    return updated_product

@router.delete("/{product_id}", response_model=product_schemas.Product) # Or perhaps just a status code 204
def delete_product(
    product_id: int, 
    db: Session = Depends(get_db)
):
    """
    Delete a product.
    This will also attempt to delete the associated inventory record.
    **Important**: If the product is part of any historical orders (OrderItems),
    the database's foreign key constraints will determine the behavior.
    - If `ON DELETE RESTRICT` (common default), deletion will fail if the product is in any order.
    - If `ON DELETE SET NULL`, the `product_id` in `OrderItems` will be set to NULL.
    - If `ON DELETE CASCADE`, `OrderItems` associated with this product would be deleted (usually not desired for sales records).
    Consider using a soft delete (marking as inactive) in a production system for products with sales history.
    """
    db_product_to_delete = crud.get_product(db, product_id=product_id)
    if db_product_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # The crud.delete_product handles inventory deletion and potential FK issues.
    # It returns the deleted product object or None if deletion failed (e.g. FK constraint).
    deleted_product = crud.delete_product(db, product_id=product_id)
    
    if deleted_product is None:
        # This implies deletion failed, likely due to FK constraints from OrderItems
        # The crud function prints an error, here we raise an HTTP Exception
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Could not delete product ID {product_id}. It might be referenced in existing orders. Check server logs for details."
        )
    return deleted_product # Return the data of the deleted product 