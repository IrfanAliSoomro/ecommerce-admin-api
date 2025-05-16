# E-commerce Admin API

This project is a back-end API designed to power a web admin dashboard for e-commerce managers. It provides insights into sales, revenue, and inventory status, and allows new product registration. The API is built using Python and FastAPI, with MySQL as the relational database.

## Core Features

1.  **Sales Status**:
    *   Endpoints to retrieve, filter, and analyze sales data.
    *   Endpoints to analyze revenue on a daily, weekly, monthly, and annual basis.
    *   Ability to compare revenue across different periods and categories.
    *   Provide sales data by date range, product, and category.
2.  **Inventory Management**:
    *   Endpoints to view current inventory status, including low stock alerts.
    *   Functionality to update inventory levels and track changes over time.
3.  **Product Management**:
    *   Endpoint to register new products.
    *   Endpoints for listing, viewing, updating, and deleting products.
4.  **Category Management**:
    *   Endpoints for creating, listing, viewing, updating, and deleting product categories.

## Technical Stack

*   **Programming Language**: Python 3.9+
*   **API Framework**: FastAPI
*   **Database**: MySQL
*   **ORM**: SQLAlchemy
*   **Data Validation**: Pydantic
*   **Server**: Uvicorn

## Project Structure

```
ecommerce_admin_api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Application settings (env vars)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy setup (engine, session)
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── crud.py             # CRUD operations for database interactions
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── product.py          # Pydantic schemas for products
│   │   ├── order.py            # Pydantic schemas for orders
│   │   ├── inventory.py        # Pydantic schemas for inventory
│   │   ├── category.py         # Pydantic schemas for categories
│   │   └── sales.py            # Pydantic schemas for sales/revenue reports
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Potential dependencies (not heavily used in this version)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/      # API endpoint modules
│   │       │   ├── __init__.py
│   │       │   ├── products.py
│   │       │   ├── orders.py
│   │       │   ├── inventory.py
│   │       │   ├── categories.py
│   │       │   └── sales_reports.py
│   │       └── api.py            # Main API router for v1
│   ├── services/               # Placeholder for business logic services
│   │   ├── __init__.py
│   └── utils.py                # Utility functions
├── scripts/
│   ├── __init__.py
│   ├── populate_db.py          # Script to populate DB with demo data
│   └── initialize_db.py        # Script to create DB tables
├── tests/                      # Placeholder for tests
│   ├── __init__.py
│   └── conftest.py
├── .env.example                # Example environment variables file
├── .gitignore
├── README.md                   # This file
└── requirements.txt            # Python dependencies
```

## Prerequisites

*   Python 3.9 or higher.
*   MySQL server (e.g., version 8.0 or higher).
*   `pip` for installing Python packages.
*   Git for cloning the repository.

## Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd ecommerce_admin_api
    ```

2.  **Create and Activate a Virtual Environment**:
    (Recommended to keep dependencies isolated)
    ```bash
    python -m venv venv
    ```
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up MySQL Database**:
    *   Ensure your MySQL server is running.
    *   Create a new database for this project. For example, using the MySQL client:
        ```sql
        CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        ```
    *   Note down the database name, username, password, host, and port.

5.  **Configure Environment Variables**:
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file with your MySQL database connection details:
        ```env
        # Database Configuration
        DATABASE_URL="mysql+pymysql://YOUR_MYSQL_USER:YOUR_MYSQL_PASSWORD@YOUR_MYSQL_HOST:YOUR_MYSQL_PORT/YOUR_DATABASE_NAME"
        # Example: DATABASE_URL="mysql+pymysql://admin_user:secretpassword@localhost:3306/ecommerce_db"

        # API Settings (defaults are usually fine)
        API_V1_STR="/api/v1"
        PROJECT_NAME="E-commerce Admin API"
        ```
        Replace placeholders with your actual credentials and database name.

6.  **Initialize Database Tables**:
    Run the script to create all necessary tables in your database based on the SQLAlchemy models:
    ```bash
    python scripts/initialize_db.py
    ```
    You should see log messages indicating successful table creation.

7.  **Populate with Demo Data (Optional but Recommended)**:
    To populate the database with sample categories, products, and orders for testing and evaluation, run:
    ```bash
    python scripts/populate_db.py
    ```
    The script will ask if you want to perform a fresh start (drop and recreate tables). If you just initialized, you can choose 'no'. If you are re-populating, 'yes' might be useful.

## Running the API

Once the setup is complete, you can start the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload
```

*   `app.main:app` tells Uvicorn where to find the FastAPI application instance (`app` in `app/main.py`).
*   `--reload` enables auto-reloading when code changes, which is useful for development.

The API will typically be available at `http://127.0.0.1:8000`.

## API Endpoints Overview

The API provides a comprehensive set of endpoints for managing e-commerce administrative tasks. For a detailed and interactive API documentation, once the server is running, navigate to:

*   **Swagger UI**: `http://127.0.0.1:8000/docs`
*   **ReDoc**: `http://127.0.0.1:8000/redoc`

Here's a summary of the main endpoint groups:

### Categories (`/api/v1/categories`)
*   `POST /`: Create a new category.
*   `GET /`: List all categories.
*   `GET /{category_id}`: Get a specific category by ID.
*   `PUT /{category_id}`: Update a category.
*   `DELETE /{category_id}`: Delete a category.

### Products (`/api/v1/products`)
*   `POST /`: Register a new product (also creates initial inventory).
*   `GET /`: List products with filtering (by category, name) and pagination.
*   `GET /{product_id}`: Get a specific product by ID.
*   `PUT /{product_id}`: Update a product's details.
*   `DELETE /{product_id}`: Delete a product (and its inventory record).

### Inventory (`/api/v1/inventory`)
*   `GET /`: View current inventory status for products (filterable by low stock, product, category).
*   `PATCH /{product_id}/`: Update inventory level for a product (adjust quantity or set absolute).
*   `GET /logs/`: View inventory change logs (filterable by product, date range, reason).

### Orders (`/api/v1/orders`)
*   `POST /`: Create a new order (updates inventory and logs changes).
*   `GET /`: List orders with filtering (by date range, status, customer) and pagination.
*   `GET /{order_id}`: Get detailed information for a specific order, including its items.

### Sales & Revenue Reports (`/api/v1/reports`)
*   `GET /sales/`: Retrieve sales data with filtering (date range, product, category) and pagination.
*   `GET /revenue/summary/`: Analyze revenue aggregated by period (daily, weekly, monthly, annually) with filtering.
*   `GET /revenue/comparison/`: Compare revenue across two different periods and/or categories.

## Database Schema Documentation

The database consists of the following main tables:

1.  **`categories`**
    *   Stores product categories.
    *   `id` (INT, PK): Unique identifier for the category.
    *   `name` (VARCHAR, Unique): Name of the category (e.g., "Electronics").
    *   `description` (TEXT, Nullable): Optional description.
    *   *Relationship*: One category can have many products.

2.  **`products`**
    *   Stores product information.
    *   `id` (INT, PK): Unique identifier for the product.
    *   `name` (VARCHAR): Name of the product.
    *   `description` (TEXT, Nullable): Detailed product description.
    *   `price` (DECIMAL): Current selling price.
    *   `category_id` (INT, FK to `categories.id`): Links product to a category.
    *   `sku` (VARCHAR, Unique, Nullable): Stock Keeping Unit.
    *   `created_at` (DATETIME): Timestamp of product creation.
    *   `updated_at` (DATETIME): Timestamp of last update.
    *   *Relationships*:
        *   Belongs to one `Category`.
        *   Has one `Inventory` record (one-to-one).
        *   Can have many `InventoryLog` entries.
        *   Can be part of many `OrderItems`.

3.  **`inventory`**
    *   Tracks current stock levels for each product.
    *   `id` (INT, PK): Unique identifier for the inventory record.
    *   `product_id` (INT, FK to `products.id`, Unique): Links to a product.
    *   `quantity` (INT): Current quantity in stock.
    *   `low_stock_threshold` (INT): Threshold for low stock alerts.
    *   `last_updated` (DATETIME): Timestamp of last inventory update.
    *   *Relationship*: Belongs to one `Product`.

4.  **`inventory_logs`**
    *   Tracks changes in inventory over time for auditing.
    *   `id` (INT, PK): Unique identifier for the log entry.
    *   `product_id` (INT, FK to `products.id`): Product whose inventory changed.
    *   `change_quantity` (INT): Amount by which quantity changed (positive for additions, negative for deductions).
    *   `new_quantity` (INT): Quantity after the change.
    *   `reason` (VARCHAR, Nullable): Reason for the change (e.g., "sale_order_#123", "manual_adjustment").
    *   `timestamp` (DATETIME): Timestamp of the inventory change.
    *   *Relationship*: Belongs to one `Product`.

5.  **`orders`**
    *   Represents a customer order.
    *   `id` (INT, PK): Unique identifier for the order.
    *   `order_date` (DATETIME): Date and time of the order.
    *   `customer_name` (VARCHAR, Nullable): Name of the customer.
    *   `status` (VARCHAR): Order status (e.g., "completed").
    *   `total_amount` (DECIMAL): Total amount for the order.
    *   *Relationship*: One order can have many `OrderItems`.

6.  **`order_items`**
    *   Represents individual line items within an order.
    *   `id` (INT, PK): Unique identifier for the order item.
    *   `order_id` (INT, FK to `orders.id`): Links to the parent order.
    *   `product_id` (INT, FK to `products.id`): Links to the product sold.
    *   `quantity` (INT): Quantity of this product sold in the order.
    *   `price_at_sale` (DECIMAL): Price per unit of the product at the time of sale.
    *   `subtotal` (DECIMAL): Calculated as `quantity * price_at_sale`.
    *   *Relationships*:
        *   Belongs to one `Order`.
        *   Refers to one `Product`.

### Indexing
Proper indexing is applied to foreign keys and columns frequently used in query filters and joins to ensure optimized performance (e.g., `categories.name`, `products.sku`, `products.name`, `orders.order_date`, `inventory_logs.timestamp`).

This structure ensures data normalization, consistency, and supports the required API functionalities.

---

This completes the core development of the E-commerce Admin API.
The next steps would typically involve more rigorous testing, potentially adding authentication/authorization, refining error handling, and preparing for deployment. 