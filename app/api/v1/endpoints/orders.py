from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import crud
from app.db.database import get_db
from app.schemas import order as order_schemas # Use the alias
from app.utils import parse_date_or_none # For parsing date query parameters

router = APIRouter()

@router.post("/", response_model=order_schemas.OrderDetails, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: order_schemas.OrderCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new order.
    - **customer_name**: Optional name of the customer.
    - **items**: A list of products to order, each with `product_id` and `quantity`.
    
    This endpoint will:
    1. Validate product existence and stock availability.
    2. Calculate total order amount based on current product prices.
    3. Create an `Order` record.
    4. Create `OrderItem` records for each product in the order.
    5. Update `Inventory` levels for sold products.
    6. Create `InventoryLog` entries for these stock changes.
    
    If any step fails (e.g., product not found, insufficient stock), the transaction is rolled back,
    and an appropriate error is returned.
    """
    try:
        created_order = crud.create_order(db=db, order_data=order_in)
        # The crud function should return the Order model instance.
        # We need to fetch related items to match OrderDetails schema.
        # A more optimized way would be to have create_order return with items already populated,
        # or have a specific get_order_details crud function.
        # For now, let's re-fetch with details.
        # However, crud.create_order is complex and might be better to adjust it to return all needed data.
        
        # Assuming crud.create_order already did the necessary refreshes to populate `items`:
        # We need to ensure the response matches OrderDetails, which includes product details in items.
        # This might require adjustments in how `crud.create_order` or schemas handle this.
        # For simplicity, let's assume create_order returns the Order object, and we construct OrderDetails.

        # Re-fetch order with details for response consistency, as crud.create_order might not fully populate nested product details
        db_order_details = crud.get_order(db, created_order.id) # This might need to be get_order_details_crud
        if not db_order_details: # Should not happen if creation was successful
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve order details after creation.")

        # Manual construction of OrderDetails if crud.get_order isn't enough
        # This is a bit verbose and ideally handled by a specific CRUD or schema transformation
        response_items = []
        for item_model in db_order_details.items:
            product_minimal = None
            if item_model.product: # Check if product relationship is loaded
                product_minimal = order_schemas.ProductMinimal.model_validate(item_model.product)
            
            response_items.append(order_schemas.OrderItem(
                id=item_model.id,
                product_id=item_model.product_id,
                quantity=item_model.quantity,
                price_at_sale=item_model.price_at_sale,
                subtotal=item_model.subtotal,
                product=product_minimal
            ))

        return order_schemas.OrderDetails(
            id=db_order_details.id,
            order_date=db_order_details.order_date,
            customer_name=db_order_details.customer_name,
            status=db_order_details.status,
            total_amount=db_order_details.total_amount,
            items=response_items
        )

    except ValueError as ve:
        # Catch specific errors raised by crud.create_order (e.g., product not found, insufficient stock)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Catch any other unexpected errors during order creation
        # Log the error e for server-side investigation
        print(f"Unexpected error during order creation: {e}") # Basic logging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the order.")


@router.get("/", response_model=List[order_schemas.Order]) # Uses the simpler Order schema for lists
def read_orders(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"), 
    limit: int = Query(100, ge=0, le=200, description="Maximum number of records to return"), 
    start_date: Optional[str] = Query(None, description="Filter orders from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter orders up to this date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter orders by status (e.g., 'completed', 'pending')"),
    customer_name_contains: Optional[str] = Query(None, description="Filter by partial customer name (case-insensitive)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of orders with pagination and filtering.
    """
    parsed_start_date = parse_date_or_none(start_date)
    parsed_end_date = parse_date_or_none(end_date)

    orders_list = crud.get_orders(
        db, skip=skip, limit=limit, 
        start_date=parsed_start_date, end_date=parsed_end_date, 
        status=status, customer_name_contains=customer_name_contains
    )
    # Augment with item_count for the Order schema if needed
    response_orders = []
    for o in orders_list:
        response_orders.append(order_schemas.Order(
            id=o.id,
            order_date=o.order_date,
            customer_name=o.customer_name,
            status=o.status,
            total_amount=o.total_amount,
            item_count=len(o.items) if o.items else 0 # Requires items to be loaded or a count query
        ))
    return response_orders

@router.get("/{order_id}", response_model=order_schemas.OrderDetails)
def read_order(
    order_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific order by its ID, including all its items and product details.
    """
    db_order = crud.get_order(db, order_id=order_id) # This should ideally load items and their products
    if db_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Transform db_order (SQLAlchemy model) to order_schemas.OrderDetails (Pydantic model)
    # This requires careful handling of nested structures like items and their products.
    response_items = []
    if db_order.items: # Ensure items relationship is loaded
        for item_model in db_order.items:
            product_minimal = None
            if item_model.product: # Ensure product relationship on item is loaded
                product_minimal = order_schemas.ProductMinimal.model_validate(item_model.product)
            
            response_items.append(order_schemas.OrderItem(
                id=item_model.id,
                product_id=item_model.product_id,
                quantity=item_model.quantity,
                price_at_sale=item_model.price_at_sale,
                subtotal=item_model.subtotal,
                product=product_minimal
            ))

    return order_schemas.OrderDetails(
        id=db_order.id,
        order_date=db_order.order_date,
        customer_name=db_order.customer_name,
        status=db_order.status,
        total_amount=db_order.total_amount,
        items=response_items
    )

# Updating an order (e.g., status) could be added here if needed.
# @router.patch("/{order_id}", response_model=order_schemas.OrderDetails)
# def update_order_status(...):
#     ...

# Deleting an order is typically not done to preserve sales history.
# Instead, orders are cancelled or refunded. 