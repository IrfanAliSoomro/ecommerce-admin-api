import logging
import random
import sys
from decimal import Decimal
from datetime import datetime, timedelta

import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base 
from app.db import crud, models
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate
from app.schemas.order import OrderCreate, OrderItemCreate
from app.core.config import settings 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CATEGORIES_DATA = [
    {"name": "Electronics", "description": "Gadgets, devices, and accessories"},
    {"name": "Books", "description": "Fiction, non-fiction, educational books"},
    {"name": "Clothing", "description": "Apparel for men, women, and children"},
    {"name": "Home & Kitchen", "description": "Appliances, decor, and kitchenware"},
    {"name": "Sports & Outdoors", "description": "Equipment for sports and outdoor activities"},
]

PRODUCTS_DATA_AMAZON_WALMART_INSPIRED = {
    "Electronics": [
        {"name": "Echo Dot (5th Gen)", "price": "49.99", "sku": "AMZ-ED5-001", "initial_quantity": 150, "low_stock_threshold": 20},
        {"name": "Kindle Paperwhite (16 GB)", "price": "139.99", "sku": "AMZ-KPW5-002", "initial_quantity": 80, "low_stock_threshold": 10},
        {"name": "Sony WH-1000XM5 Headphones", "price": "348.00", "sku": "SONY-XM5-001", "initial_quantity": 60, "low_stock_threshold": 5},
        {"name": "Samsung 55-Inch QLED 4K TV", "price": "797.99", "sku": "SAM-QLED55-001", "initial_quantity": 30, "low_stock_threshold": 3},
    ],
    "Books": [
        {"name": "Atomic Habits by James Clear", "price": "13.79", "sku": "BK-AHJC-001", "initial_quantity": 200, "low_stock_threshold": 25},
        {"name": "The Midnight Library by Matt Haig", "price": "15.62", "sku": "BK-TMLMH-001", "initial_quantity": 120, "low_stock_threshold": 15},
        {"name": "Python Crash Course, 3rd Edition", "price": "31.99", "sku": "BK-PCC3-001", "initial_quantity": 90, "low_stock_threshold": 10},
    ],
    "Clothing": [
        {"name": "Levi's Men's 501 Original Fit Jeans", "price": "59.50", "sku": "LEV-M501-001", "initial_quantity": 100, "low_stock_threshold": 10},
        {"name": "Amazon Essentials Women's Classic T-Shirt (2-Pack)", "price": "18.90", "sku": "AMZ-WCT2P-001", "initial_quantity": 300, "low_stock_threshold": 30},
    ],
    "Home & Kitchen": [
        {"name": "Instant Pot Duo 7-in-1 Electric Pressure Cooker", "price": "89.00", "sku": "IP-DUO71-001", "initial_quantity": 70, "low_stock_threshold": 7},
        {"name": "Keurig K-Mini Coffee Maker", "price": "79.99", "sku": "KEU-KMINI-001", "initial_quantity": 110, "low_stock_threshold": 10},
    ],
    "Sports & Outdoors": [
        {"name": "YETI Rambler 30 oz Tumbler", "price": "38.00", "sku": "YETI-RAM30-001", "initial_quantity": 130, "low_stock_threshold": 15},
        {"name": "Spalding Street Outdoor Basketball", "price": "24.99", "sku": "SPA-SOB-001", "initial_quantity": 160, "low_stock_threshold": 20},
    ]
}

def populate_db(db: Session, fresh_start: bool = False):
    logger.info(f"Starting database population process. Fresh start: {fresh_start}")
    if fresh_start:
        logger.info("Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine) 
        logger.info("Creating all tables...")
        Base.metadata.create_all(bind=engine) 
        logger.info("Tables recreated.")

 
    logger.info("Creating categories...")
    created_categories = {}
    for cat_data in CATEGORIES_DATA:
        category = crud.get_category_by_name(db, name=cat_data["name"])
        if not category:
            category = crud.create_category(db, CategoryCreate(**cat_data))
            logger.info(f"Created category: {category.name}")
        else:
            logger.info(f"Category '{category.name}' already exists, skipping.")
        created_categories[category.name] = category
    logger.info("Categories created/verified.")


    logger.info("Creating products...")
    created_products_map = {} 
    for cat_name, products_list in PRODUCTS_DATA_AMAZON_WALMART_INSPIRED.items():
        category_model = created_categories.get(cat_name)
        if not category_model:
            logger.warning(f"Category '{cat_name}' not found. Skipping products for this category.")
            continue
        
        for prod_data in products_list:
            product = crud.get_product_by_sku(db, sku=prod_data["sku"])
            if not product:
                product_create_schema = ProductCreate(
                    name=prod_data["name"],
                    price=Decimal(prod_data["price"]),
                    category_id=category_model.id,
                    sku=prod_data["sku"],
                    description=prod_data.get("description", "-"),
                    initial_quantity=prod_data["initial_quantity"],
                    low_stock_threshold=prod_data["low_stock_threshold"]
                )
                product = crud.create_product(db, product=product_create_schema)
                logger.info(f"Created product: {product.name} (SKU: {product.sku})")
            else:
                logger.info(f"Product '{product.name}' (SKU: {product.sku}) already exists, skipping.")
            created_products_map[product.sku] = product
    logger.info("Products created/verified.")

    logger.info("Creating sample orders...")
    num_sample_orders = 25 
    all_product_skus = list(created_products_map.keys())

    if not all_product_skus:
        logger.warning("No products available to create sample orders. Skipping order creation.")
        return

    customer_names = ["Alice Smith", "Bob Johnson", "Carol Williams", "David Brown", "Eva Jones", "Global Mart Inc.", "Tech Solutions Ltd."]

    for i in range(num_sample_orders):
        num_items_in_order = random.randint(1, 4)
        order_items_data = []
      
        sample_size = min(num_items_in_order, len(all_product_skus))
        potential_order_skus = random.sample(all_product_skus, sample_size)
        
        customer_name = random.choice(customer_names)

        for sku in potential_order_skus:
            product_model = created_products_map[sku]
            inventory_record = crud.get_inventory_by_product_id(db, product_model.id)
            
            if inventory_record and inventory_record.quantity > 0:
                max_qty_orderable = min(3, inventory_record.quantity)
                quantity_to_order = random.randint(1, max_qty_orderable) 
                order_items_data.append(OrderItemCreate(product_id=product_model.id, quantity=quantity_to_order))

        if order_items_data: 
            order_create_schema = OrderCreate(customer_name=f"{customer_name} (Order #{i+1})", items=order_items_data)
            try:
                order = crud.create_order(db, order_data=order_create_schema)
                logger.info(f"Created Order ID: {order.id} with {len(order.items)} items, Total: {order.total_amount}")
                random_days_ago = random.randint(0, 365)
                random_hours_ago = random.randint(0,23)
                random_minutes_ago = random.randint(0,59)
                order.order_date = datetime.now() - timedelta(days=random_days_ago, hours=random_hours_ago, minutes=random_minutes_ago)
                db.commit() 
                db.refresh(order) 

            except ValueError as ve: 
                logger.warning(f"Could not create sample order #{i+1} due to: {ve}")
            except Exception as e:
                logger.error(f"Unexpected error creating sample order #{i+1}: {e}")
        else:
            logger.info(f"Skipped creating sample order #{i+1} as no items had sufficient stock or were selected.")

    logger.info(f"Sample orders creation process completed ({num_sample_orders} attempts).")
    logger.info("Database population complete.")

if __name__ == "__main__":
    logger.info("Starting script to populate the database with demo data.")
    db = SessionLocal()
    try:
        choice = input("Do you want to perform a fresh start (drop and recreate all tables before populating)? (yes/no) [no]: ").strip().lower()
        perform_fresh_start = choice == 'yes'
        
        populate_db(db, fresh_start=perform_fresh_start)
    except Exception as e:
        logger.error(f"An error occurred during the data population process: {e}", exc_info=True)
    finally:
        db.close()
        logger.info("Database session closed.") 