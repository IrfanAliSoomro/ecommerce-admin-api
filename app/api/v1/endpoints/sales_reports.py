from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from decimal import Decimal

from app.db import crud
from app.db.database import get_db
from app.schemas import sales as sales_schemas # Use the alias
from app.utils import parse_date_or_none # For parsing date query parameters

router = APIRouter()

@router.get("/sales/", response_model=sales_schemas.SalesDataResponse)
def get_sales_data_report(
    start_date: Optional[str] = Query(None, description="Start date for sales data (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for sales data (YYYY-MM-DD)"),
    product_id: Optional[int] = Query(None, description="Filter sales by a specific product ID"),
    category_id: Optional[int] = Query(None, description="Filter sales by a specific category ID"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db)
):
    """
    Retrieve, filter, and analyze sales data.
    Provides sales data by date range, product, and category with pagination.
    """
    parsed_start_date = parse_date_or_none(start_date)
    parsed_end_date = parse_date_or_none(end_date)

    if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date.")

    sales_data_paginated = crud.get_sales_data(
        db,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        product_id=product_id,
        category_id=category_id,
        page=page,
        page_size=page_size
    )
    
    # Convert SQLAlchemy Row objects to Pydantic models if needed (CRUD should handle this)
    # The crud.get_sales_data should return a dict that matches SalesDataResponse structure directly or its items part.
    # Assuming crud.get_sales_data returns a dict like: 
    # {"total_items": ..., "items": [RowProxy...], "page": ..., ...}
    # We need to convert items if they are not already Pydantic models.

    response_items = []
    for item_row in sales_data_paginated["items"]:
        response_items.append(sales_schemas.SaleItemDetail.model_validate(item_row)) # Use model_validate for RowProxy

    return sales_schemas.SalesDataResponse(
        total_items=sales_data_paginated["total_items"],
        items=response_items,
        page=sales_data_paginated["page"],
        page_size=sales_data_paginated["page_size"],
        num_pages=sales_data_paginated["num_pages"]
    )

@router.get("/revenue/summary/", response_model=sales_schemas.RevenueSummaryResponse)
def get_revenue_summary_report(
    period: str = Query(..., description="Aggregation period: 'daily', 'weekly', 'monthly', or 'annually'"),
    start_date_str: str = Query(..., alias="start_date", description="Start date for the analysis (YYYY-MM-DD)"),
    end_date_str: str = Query(..., alias="end_date", description="End date for the analysis (YYYY-MM-DD)"),
    category_id: Optional[int] = Query(None, description="Filter revenue by a specific category ID"),
    db: Session = Depends(get_db)
):
    """
    Analyze revenue on a daily, weekly, monthly, or annual basis.
    """
    start_date = parse_date_or_none(start_date_str)
    end_date = parse_date_or_none(end_date_str)

    if not start_date or not end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid start_date and end_date (YYYY-MM-DD) are required.")
    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date.")
    
    allowed_periods = ["daily", "weekly", "monthly", "annually"]
    if period.lower() not in allowed_periods:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid period. Allowed periods are: {', '.join(allowed_periods)}")

    try:
        revenue_data = crud.get_revenue_summary(
            db, period=period.lower(), start_date=start_date, end_date=end_date, category_id=category_id
        )
        # The CRUD function now returns a list of dicts that should match RevenueDataPoint structure
        # after internal conversion of date/datetime to ISO strings.
        
        # Calculate overall total for the response if needed
        overall_total = sum(Decimal(item['total_revenue']) for item in revenue_data) if revenue_data else Decimal("0.00")

        return sales_schemas.RevenueSummaryResponse(
            data=[sales_schemas.RevenueDataPoint(**item) for item in revenue_data],
            overall_total_revenue=overall_total
            )

    except ValueError as ve: # Catch errors from CRUD like invalid period
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log e
        print(f"Error in revenue summary: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing revenue summary.")

@router.get("/revenue/comparison/", response_model=sales_schemas.RevenueComparisonResponse)
def get_revenue_comparison_report(
    period1_start_date_str: str = Query(..., alias="p1_start_date", description="Period 1 Start Date (YYYY-MM-DD)"),
    period1_end_date_str: str = Query(..., alias="p1_end_date", description="Period 1 End Date (YYYY-MM-DD)"),
    period2_start_date_str: str = Query(..., alias="p2_start_date", description="Period 2 Start Date (YYYY-MM-DD)"),
    period2_end_date_str: str = Query(..., alias="p2_end_date", description="Period 2 End Date (YYYY-MM-DD)"),
    category_id1: Optional[int] = Query(None, description="Category ID for Period 1 (optional)"),
    category_id2: Optional[int] = Query(None, description="Category ID for Period 2 (optional, defaults to category_id1 if comparing same category)"),
    db: Session = Depends(get_db)
):
    """
    Compare revenue across different periods and/or categories.
    """
    p1_start = parse_date_or_none(period1_start_date_str)
    p1_end = parse_date_or_none(period1_end_date_str)
    p2_start = parse_date_or_none(period2_start_date_str)
    p2_end = parse_date_or_none(period2_end_date_str)

    if not all([p1_start, p1_end, p2_start, p2_end]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All date parameters are required and must be valid (YYYY-MM-DD).")
    if p1_start > p1_end or p2_start > p2_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date for any period.")

    # If category_id2 is not provided but category_id1 is, assume comparison for the same category
    if category_id1 is not None and category_id2 is None:
        category_id2 = category_id1
    
    try:
        rev1, cat1_name = crud.get_revenue_for_period(db, start_date=p1_start, end_date=p1_end, category_id=category_id1)
        rev2, cat2_name = crud.get_revenue_for_period(db, start_date=p2_start, end_date=p2_end, category_id=category_id2)

        difference = rev2 - rev1
        percentage_change = 0.0
        if rev1 > 0: # Avoid division by zero
            percentage_change = round((difference / rev1) * 100, 2)
        elif rev2 > 0: # If rev1 is 0 but rev2 is positive, it's an infinite percentage increase practically
            percentage_change = float('inf') # Or handle as 100% or a large number depending on preference

        return sales_schemas.RevenueComparisonResponse(
            period1_start_date=p1_start,
            period1_end_date=p1_end,
            period1_revenue=rev1,
            period1_category_name=cat1_name,
            period2_start_date=p2_start,
            period2_end_date=p2_end,
            period2_revenue=rev2,
            period2_category_name=cat2_name,
            difference=difference,
            percentage_change=percentage_change
        )
    except Exception as e:
        # Log e
        print(f"Error in revenue comparison: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing revenue comparison.") 