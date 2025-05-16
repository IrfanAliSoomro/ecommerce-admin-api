import datetime
from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from .database import Base # Ensure this import is correct based on your file structure

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    sku = Column(String(100), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False) # One-to-one
    inventory_logs = relationship("InventoryLog", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, nullable=False, default=10)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="inventory")

class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    change_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=func.now(), index=True)

    product = relationship("Product", back_populates="inventory_logs")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_date = Column(DateTime, nullable=False, default=func.now(), index=True)
    customer_name = Column(String(255), nullable=True)
    # In a real app, status would likely be an Enum or a separate table
    status = Column(String(50), default='completed', nullable=False, index=True)
    total_amount = Column(DECIMAL(10, 2), nullable=False)

    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price_at_sale = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False) # quantity * price_at_sale

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items") 