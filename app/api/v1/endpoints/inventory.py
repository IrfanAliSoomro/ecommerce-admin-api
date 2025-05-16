from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import crud
from app.db.database import get_db
from app.schemas import inventory as inventory_schemas # Use the alias
from app.schemas import product as product_schemas # To validate product existence

router = APIRouter()

@router.get("/", response_model=List[inventory_schemas.Inventory])
def read_inventory_status(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"), 
    limit: int = Query(100, ge=0, le=200, description="Maximum number of records to return"), 
    low_stock: Optional[bool] = Query(None, description="Filter by low stock status. True for low stock, False for not low, omit for all."),
    product_id: Optional[int] = Query(None, description="Filter by a specific product ID"),
    category_id: Optional[int] = Query(None, description="Filter by products in a specific category ID"),
    db: Session = Depends(get_db)
):
    """
    View current inventory status for products.
    - Supports pagination.
    - Can filter by `low_stock` status (quantity <= low_stock_threshold).
    - Can filter by `product_id` or `category_id`.
    """
    inventory_list = crud.get_all_inventory_status(
        db, skip=skip, limit=limit, low_stock=low_stock, product_id=product_id, category_id=category_id
    )
    
    # Augment with is_low_stock flag for the response schema
    response_list = []
    for inv_item in inventory_list:
        is_low = inv_item.quantity <= inv_item.low_stock_threshold
        # Re-serialize to fit the response schema properly, including product and is_low_stock
        # This ensures that the nested ProductMinimal schema is also correctly populated.
        product_data = product_schemas.ProductMinimal.model_validate(inv_item.product) if inv_item.product else None
        inv_response_item = inventory_schemas.Inventory(
            id=inv_item.id,
            product_id=inv_item.product_id,
            quantity=inv_item.quantity,
            low_stock_threshold=inv_item.low_stock_threshold,
            last_updated=inv_item.last_updated,
            product=product_data,
            is_low_stock=is_low
        )
        response_list.append(inv_response_item)
    return response_list

@router.patch("/{product_id}/", response_model=inventory_schemas.Inventory)
def update_inventory_level(
    product_id: int, 
    inventory_in: inventory_schemas.InventoryUpdate, 
    db: Session = Depends(get_db)
):
    """
    Manually update the inventory level for a specific product.
    Use `quantity_change` for relative adjustments (e.g., +50 or -10).
    Use `absolute_quantity` to set a new total stock level.
    Provide one or the other, not both. 
    `low_stock_threshold` can also be updated.
    A reason for the update can be provided for logging purposes.
    """
    db_product = crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found.")

    if inventory_in.quantity_change is not None and inventory_in.absolute_quantity is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide either 'quantity_change' or 'absolute_quantity', not both.")
    if inventory_in.quantity_change is None and inventory_in.absolute_quantity is None and inventory_in.low_stock_threshold is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update operation specified. Provide 'quantity_change', 'absolute_quantity', or 'low_stock_threshold'.")

    updated_inventory = crud.update_inventory(db=db, product_id=product_id, inventory_update=inventory_in)
    if not updated_inventory:
        # This case should ideally be caught by product check, but as a fallback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory record not found for product ID {product_id}. This shouldn't happen if product exists.")
    
    # Augment for response
    is_low = updated_inventory.quantity <= updated_inventory.low_stock_threshold
    product_data = product_schemas.ProductMinimal.model_validate(updated_inventory.product) if updated_inventory.product else None
    response_item = inventory_schemas.Inventory(
        id=updated_inventory.id,
        product_id=updated_inventory.product_id,
        quantity=updated_inventory.quantity,
        low_stock_threshold=updated_inventory.low_stock_threshold,
        last_updated=updated_inventory.last_updated,
        product=product_data,
        is_low_stock=is_low
    )
    return response_item

@router.get("/logs/", response_model=List[inventory_schemas.InventoryLog])
def read_inventory_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"), 
    limit: int = Query(100, ge=0, le=500, description="Maximum number of records to return"), 
    product_id: Optional[int] = Query(None, description="Filter logs by a specific product ID"),
    start_date: Optional[str] = Query(None, description="Filter logs from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter logs up to this date (YYYY-MM-DD)"),
    reason_contains: Optional[str] = Query(None, description="Filter logs by keywords in the reason field (case-insensitive)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a log of all inventory changes with pagination and filtering.
    Allows filtering by product, date range, and reason.
    """
    from app.utils import parse_date_or_none # Helper to parse date strings

    parsed_start_date = parse_date_or_none(start_date)
    parsed_end_date = parse_date_or_none(end_date)

    logs = crud.get_inventory_logs(
        db, 
        skip=skip, 
        limit=limit, 
        product_id=product_id, 
        start_date=parsed_start_date, 
        end_date=parsed_end_date, 
        reason_contains=reason_contains
    )
    # Map to response schema, potentially fetching product names
    response_logs = []
    for log_entry in logs:
        product_name = log_entry.product.name if log_entry.product else None # Assuming relationship is loaded or accessible
        response_logs.append(
            inventory_schemas.InventoryLog(
                id=log_entry.id,
                product_id=log_entry.product_id,
                product_name=product_name,
                change_quantity=log_entry.change_quantity,
                new_quantity=log_entry.new_quantity,
                reason=log_entry.reason,
                timestamp=log_entry.timestamp
            )
        )
    return response_logs 