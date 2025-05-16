from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import crud, models
from app.db.database import get_db
from app.schemas import category as category_schemas # Use the alias

router = APIRouter()

@router.post("/", response_model=category_schemas.Category, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: category_schemas.CategoryCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new category.
    - **name**: Each category must have a unique name.
    - **description**: Optional description for the category.
    """
    db_category = crud.get_category_by_name(db, name=category_in.name)
    if db_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category with name '{category_in.name}' already exists.")
    return crud.create_category(db=db, category=category_in)

@router.get("/", response_model=List[category_schemas.Category])
def read_categories(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"), 
    limit: int = Query(100, ge=0, le=200, description="Maximum number of records to return"), 
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of all categories with pagination.
    """
    categories = crud.get_categories(db, skip=skip, limit=limit)
    return categories

@router.get("/{category_id}", response_model=category_schemas.Category)
def read_category(
    category_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get a specific category by its ID.
    """
    db_category = crud.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return db_category

@router.put("/{category_id}", response_model=category_schemas.Category)
def update_category(
    category_id: int, 
    category_in: category_schemas.CategoryUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update an existing category.
    Allows partial updates. Only fields present in the request body will be updated.
    """
    db_category = crud.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Check if new name conflicts with an existing category (if name is being changed)
    if category_in.name and category_in.name != db_category.name:
        existing_category = crud.get_category_by_name(db, name=category_in.name)
        if existing_category and existing_category.id != category_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category name '{category_in.name}' already taken.")
            
    updated_category = crud.update_category(db=db, category_id=category_id, category_update=category_in)
    return updated_category

@router.delete("/{category_id}", response_model=category_schemas.Category)
def delete_category(
    category_id: int, 
    db: Session = Depends(get_db)
):
    """
    Delete a category.
    Note: This will fail if the category is currently associated with any products 
    (due to foreign key constraints), unless those constraints are set to SET NULL or CASCADE.
    Consider implementing logic to reassign products or prevent deletion if in use.
    """
    # Check if category is in use by products
    products_in_category = db.query(models.Product).filter(models.Product.category_id == category_id).first()
    if products_in_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Cannot delete category. It is currently associated with product(s) like '{products_in_category.name}'. Reassign products first."
        )

    db_category = crud.delete_category(db, category_id=category_id)
    if db_category is None: # Should be caught by the check above if it was a FK issue, but good for direct not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return db_category 