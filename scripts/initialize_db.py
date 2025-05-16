import logging
import sys

import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.db.database import engine, Base, SessionLocal
from app.db import models 
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info(f"Initializing database at {settings.DATABASE_URL}...")
    logger.info("This will create all tables defined in SQLAlchemy models.")
    logger.info("For production, consider using Alembic for migrations.")

    try:

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
        
      
        db = SessionLocal()

        count = db.query(models.Category).count()
        logger.info(f"Successfully connected and queried 'categories' table (found {count} initial records).")
        db.close()
        logger.info("Database initialization complete.")

    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        logger.error("Please ensure your database server is running and the DATABASE_URL in your .env file is correct.")
        sys.exit(1) 

if __name__ == "__main__":
    
    print("Running database initializer...")
    init_db() 


