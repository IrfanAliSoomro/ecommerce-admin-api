from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from decimal import Decimal
import datetime
from typing import List, Optional, Dict, Any, Tuple

from . import models
from app.schemas import category as category_schemas 
from app.schemas import product as product_schemas   
from app.schemas import order as order_schemas
from app.schemas import inventory as inventory_schemas

def get_paginated_items(query, page: int, page_size: int):
    total_items = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    num_pages = (total_items + page_size - 1) // page_size
    return {
        "total_items": total_items,
        "items": items,
        "page": page,
        "page_size": page_size,
        "num_pages": num_pages
    }



def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_category_by_name(db: Session, name: str) -> Optional[models.Category]:
    return db.query(models.Category).filter(func.lower(models.Category.name) == func.lower(name)).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[models.Category]:
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: category_schemas.CategoryCreate) -> models.Category:
    db_category = models.Category(name=category.name, description=category.description)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, category_update: category_schemas.CategoryUpdate) -> Optional[models.Category]:
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int) -> Optional[models.Category]:
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    db.delete(db_category)
    db.commit()
    return db_category


def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_product_by_sku(db: Session, sku: str) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.sku == sku).first()

def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    name_contains: Optional[str] = None
) -> List[models.Product]:
    query = db.query(models.Product)
    if category_id is not None:
        query = query.filter(models.Product.category_id == category_id)
    if name_contains:
        query = query.filter(models.Product.name.ilike(f"%{name_contains}%")) # Case-insensitive search
    return query.order_by(models.Product.name).offset(skip).limit(limit).all()

def create_product(db: Session, product: product_schemas.ProductCreate) -> models.Product:
    db_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        category_id=product.category_id,
        sku=product.sku
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    db_inventory = models.Inventory(
        product_id=db_product.id, 
        quantity=product.initial_quantity,
        low_stock_threshold=product.low_stock_threshold if product.low_stock_threshold is not None else 10
    )
    db.add(db_inventory)
    

    db_inventory_log = models.InventoryLog(
        product_id=db_product.id,
        change_quantity=product.initial_quantity,
        new_quantity=product.initial_quantity,
        reason="Initial stock"
    )
    db.add(db_inventory_log)
    
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: product_schemas.ProductUpdate) -> Optional[models.Product]:
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int) -> Optional[models.Product]:
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    db_inventory = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if db_inventory:
        db.delete(db_inventory)
    try:
        db.delete(db_product)
        db.commit()
        return db_product 
    except Exception as e:
        db.rollback() 
        print(f"Error deleting product {product_id}: {e}")
        return None




def get_inventory_by_product_id(db: Session, product_id: int) -> Optional[models.Inventory]:
    return db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()

def get_all_inventory_status(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    low_stock: Optional[bool] = None,
    product_id: Optional[int] = None,
    category_id: Optional[int] = None
) -> List[models.Inventory]:
    query = db.query(models.Inventory).join(models.Product) 

    if product_id is not None:
        query = query.filter(models.Inventory.product_id == product_id)
    
    if category_id is not None:
        query = query.filter(models.Product.category_id == category_id)

    if low_stock is True:
        query = query.filter(models.Inventory.quantity <= models.Inventory.low_stock_threshold)
    elif low_stock is False: 
        query = query.filter(models.Inventory.quantity > models.Inventory.low_stock_threshold)

    return query.order_by(models.Inventory.product_id).offset(skip).limit(limit).all()


def update_inventory(
    db: Session, 
    product_id: int, 
    inventory_update: inventory_schemas.InventoryUpdate
) -> Optional[models.Inventory]:
    db_inventory = get_inventory_by_product_id(db, product_id)
    if not db_inventory:
        return None 

    original_quantity = db_inventory.quantity
    new_quantity = original_quantity
    log_reason = inventory_update.reason or "Manual update"

    if inventory_update.quantity_change is not None:
        new_quantity += inventory_update.quantity_change
    elif inventory_update.absolute_quantity is not None:
        new_quantity = inventory_update.absolute_quantity
    else:
        pass 

    if new_quantity < 0:
        new_quantity = 0 

    change_quantity = new_quantity - original_quantity
    db_inventory.quantity = new_quantity
    
    if inventory_update.low_stock_threshold is not None:
        db_inventory.low_stock_threshold = inventory_update.low_stock_threshold

    db_inventory.last_updated = func.now() 

    if change_quantity != 0 or (inventory_update.quantity_change is not None and inventory_update.quantity_change != 0) or (inventory_update.absolute_quantity is not None and inventory_update.absolute_quantity != original_quantity):
        db_inventory_log = models.InventoryLog(
            product_id=product_id,
            change_quantity=change_quantity,
            new_quantity=new_quantity,
            reason=log_reason,
            timestamp=func.now() 
        )
        db.add(db_inventory_log)
    
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def get_inventory_logs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    product_id: Optional[int] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    reason_contains: Optional[str] = None
) -> List[models.InventoryLog]:
    query = db.query(models.InventoryLog)
    if product_id is not None:
        query = query.filter(models.InventoryLog.product_id == product_id)
    if start_date:
        query = query.filter(models.InventoryLog.timestamp >= datetime.datetime.combine(start_date, datetime.time.min))
    if end_date:
        query = query.filter(models.InventoryLog.timestamp <= datetime.datetime.combine(end_date, datetime.time.max))
    if reason_contains:
        query = query.filter(models.InventoryLog.reason.ilike(f"%{reason_contains}%"))
    
    return query.order_by(models.InventoryLog.timestamp.desc()).offset(skip).limit(limit).all()

# --- Order CRUD --- 

def create_order(db: Session, order_data: order_schemas.OrderCreate) -> models.Order:

    total_order_amount = Decimal("0.00")
    order_items_to_create = []
    inventory_updates_needed = [] 

    for item_data in order_data.items:
        db_product = get_product(db, item_data.product_id)
        if not db_product:
            raise ValueError(f"Product with ID {item_data.product_id} not found.") 
        
        db_inventory = get_inventory_by_product_id(db, item_data.product_id)
        if not db_inventory or db_inventory.quantity < item_data.quantity:
            raise ValueError(f"Not enough stock for product {db_product.name} (ID: {item_data.product_id}). Available: {db_inventory.quantity if db_inventory else 0}, Requested: {item_data.quantity}")

        price_at_sale = db_product.price
        subtotal = price_at_sale * item_data.quantity
        total_order_amount += subtotal

        order_items_to_create.append({
            "product_id": item_data.product_id,
            "quantity": item_data.quantity,
            "price_at_sale": price_at_sale,
            "subtotal": subtotal
        })
        inventory_updates_needed.append((item_data.product_id, item_data.quantity, db_inventory.quantity))

    # Create the Order record
    db_order = models.Order(
        customer_name=order_data.customer_name,
        total_amount=total_order_amount,
        status='completed' 
    )
    db.add(db_order)
    db.commit() 
    db.refresh(db_order)

    for item_info in order_items_to_create:
        db_order_item = models.OrderItem(
            order_id=db_order.id,
            **item_info
        )
        db.add(db_order_item)

    for product_id, quantity_deducted, original_inv_qty in inventory_updates_needed:
        db_inventory = get_inventory_by_product_id(db, product_id) 
        if db_inventory: 
            new_inv_quantity = db_inventory.quantity - quantity_deducted
            db_inventory.quantity = new_inv_quantity
            db_inventory.last_updated = func.now()

            inventory_log = models.InventoryLog(
                product_id=product_id,
                change_quantity=-quantity_deducted,
                new_quantity=new_inv_quantity,
                reason=f"Sale - Order ID: {db_order.id}",
                timestamp=func.now()
            )
            db.add(inventory_log)

    db.commit() 
    db.refresh(db_order)
    return db_order

def get_order(db: Session, order_id: int) -> Optional[models.Order]:
    return (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .first()
    )

def get_orders(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    status: Optional[str] = None,
    customer_name_contains: Optional[str] = None,
) -> List[models.Order]:
    query = db.query(models.Order)
    if start_date:
        query = query.filter(models.Order.order_date >= datetime.datetime.combine(start_date, datetime.time.min))
    if end_date:
        query = query.filter(models.Order.order_date <= datetime.datetime.combine(end_date, datetime.time.max))
    if status:
        query = query.filter(models.Order.status.ilike(f"%{status}%"))
    if customer_name_contains:
        query = query.filter(models.Order.customer_name.ilike(f"%{customer_name_contains}%"))
    
    return query.order_by(models.Order.order_date.desc()).offset(skip).limit(limit).all()



def get_sales_data(
    db: Session, 
    start_date: Optional[datetime.date] = None, 
    end_date: Optional[datetime.date] = None, 
    product_id: Optional[int] = None, 
    category_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    query = (
        db.query(
            models.OrderItem.order_id,
            models.Order.order_date,
            models.OrderItem.product_id,
            models.Product.name.label("product_name"),
            models.Product.category_id,
            models.Category.name.label("category_name"),
            models.OrderItem.quantity.label("quantity_sold"),
            models.OrderItem.price_at_sale,
            models.OrderItem.subtotal
        )
        .join(models.Order, models.OrderItem.order_id == models.Order.id)
        .join(models.Product, models.OrderItem.product_id == models.Product.id)
        .join(models.Category, models.Product.category_id == models.Category.id)
    )

    if start_date:
        query = query.filter(models.Order.order_date >= datetime.datetime.combine(start_date, datetime.time.min))
    if end_date:
        query = query.filter(models.Order.order_date <= datetime.datetime.combine(end_date, datetime.time.max))
    if product_id:
        query = query.filter(models.OrderItem.product_id == product_id)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)

    query = query.order_by(models.Order.order_date.desc())
    
    return get_paginated_items(query, page, page_size)


def get_revenue_summary(
    db: Session, 
    period: str, 
    start_date: datetime.date, 
    end_date: datetime.date, 
    category_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    
    date_trunc_formats = {
        "daily": func.date(models.Order.order_date),
        "weekly": func.date_trunc('week', models.Order.order_date),
        "monthly": func.date_trunc('month', models.Order.order_date),
        "annually": func.date_trunc('year', models.Order.order_date),
    }

    if period not in date_trunc_formats:
        raise ValueError("Invalid period specified. Choose from daily, weekly, monthly, annually.")

    period_trunc = date_trunc_formats[period]

    query = (
        db.query(
            period_trunc.label("period_start"),
            func.sum(models.OrderItem.subtotal).label("total_revenue"),
            models.Category.name.label("category_name") if category_id else func.lit(None).label("category_name")
        )
        .join(models.OrderItem, models.Order.id == models.OrderItem.order_id)
        .join(models.Product, models.OrderItem.product_id == models.Product.id)
    )

    query = query.filter(models.Order.order_date >= datetime.datetime.combine(start_date, datetime.time.min))
    query = query.filter(models.Order.order_date <= datetime.datetime.combine(end_date, datetime.time.max))

    if category_id:
        query = query.join(models.Category, models.Product.category_id == models.Category.id)
        query = query.filter(models.Product.category_id == category_id)
        query = query.group_by("period_start", models.Category.name) # Group by category name as well
    else:
        query = query.group_by("period_start")

    query = query.order_by("period_start")
    
    results = query.all()


    formatted_results = []
    for row in results:
        ps = row.period_start
        pe = ps 
        if period == "weekly":
            if isinstance(ps, datetime.datetime):
                pe = ps + datetime.timedelta(days=6)
            elif isinstance(ps, datetime.date):
                 pe = ps + datetime.timedelta(days=6) 
        elif period == "monthly":
            if isinstance(ps, datetime.datetime):
                next_month = ps.replace(day=28) + datetime.timedelta(days=4) 
                pe = next_month - datetime.timedelta(days=next_month.day) 
            elif isinstance(ps, datetime.date):
                next_month = ps.replace(day=28) + datetime.timedelta(days=4)
                pe = next_month - datetime.timedelta(days=next_month.day)
        elif period == "annually":
            if isinstance(ps, datetime.datetime):
                pe = ps.replace(month=12, day=31)
            elif isinstance(ps, datetime.date):
                pe = ps.replace(month=12, day=31)

        formatted_results.append({
            "period_start": ps.isoformat() if ps else None, 
            "period_end": pe.isoformat() if pe else None,
            "total_revenue": row.total_revenue,
            "category_name": row.category_name
        })
    return formatted_results


def get_revenue_for_period(
    db: Session, 
    start_date: datetime.date, 
    end_date: datetime.date, 
    category_id: Optional[int] = None
) -> Tuple[Decimal, Optional[str]]:
    query = (
        db.query(func.sum(models.OrderItem.subtotal).label("total_revenue"))
        .join(models.Order, models.OrderItem.order_id == models.Order.id)
        .join(models.Product, models.OrderItem.product_id == models.Product.id)
    )
    query = query.filter(models.Order.order_date >= datetime.datetime.combine(start_date, datetime.time.min))
    query = query.filter(models.Order.order_date <= datetime.datetime.combine(end_date, datetime.time.max))
    
    category_name = None
    if category_id:
        query = query.join(models.Category, models.Product.category_id == models.Category.id)
        query = query.filter(models.Product.category_id == category_id)
        cat = db.query(models.Category.name).filter(models.Category.id == category_id).first()
        if cat:
            category_name = cat[0]

    result = query.scalar_one_or_none() 
    return result if result is not None else Decimal("0.00"), category_name 