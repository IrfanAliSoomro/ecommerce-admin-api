from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import database, models 
from app.api.v1 import api as api_v1 


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_v1.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    print(f"Application startup: {settings.PROJECT_NAME} is ready.")
    try:
        db = database.SessionLocal()
        db.query(models.Category).first() 
        print("Database connection successful.")
    except Exception as e:
        print(f"Error connecting to the database or tables might not exist: {e}")
        print("Please ensure the database is running and tables are created (e.g., using 'initialize_db.py' or Alembic migrations).")
    finally:
        if 'db' in locals() and db is not None:
            db.close()

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME}! Navigate to /docs for API documentation."}

