from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings # Corrected import path

# Create a SQLAlchemy engine
# The pool_pre_ping argument will test connections in the pool for liveness 
# and transparently re-establish them if they are stale.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    # connect_args={"check_same_thread": False} # Only for SQLite, not needed for MySQL
)

# Create a configured "SessionLocal" class
# This session will be the actual database session.
# autocommit=False and autoflush=False are standard for web applications, giving more control.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our SQLAlchemy models
# All our database model classes will inherit from this.
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 