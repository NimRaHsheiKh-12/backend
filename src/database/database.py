# src/database/database.py

import os
import logging
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv  # << Add this

# Load environment variables from .env
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# =============================
# DATABASE CONFIGURATION
# =============================
DATABASE_URL = os.getenv("DATABASE_URL")  # Railway or other remote DB URL
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "False") == "True"

# Helper to create an engine with consistent options
def _make_engine(url: str):
    return create_engine(
        url,
        poolclass=QueuePool,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=20,
        max_overflow=30,
        echo=DATABASE_ECHO,
    )

# Try to use DATABASE_URL first; if it's missing or unreachable, fall back to SQLite
engine = None
if DATABASE_URL:
    try:
        tmp_engine = _make_engine(DATABASE_URL)
        # quick connectivity test
        with tmp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine = tmp_engine
        logger.info("Using DATABASE_URL from environment")
    except Exception as e:
        logger.error(f"Cannot connect to DATABASE_URL: {e}. Falling back to SQLite.")

if engine is None:
    sqlite_url = os.getenv("SQLITE_URL", "sqlite:///./dev.db")
    engine = _make_engine(sqlite_url)
    logger.info(f"Using SQLite database at {sqlite_url}")

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# =============================
# DATABASE DEPENDENCIES
# =============================
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for non-FastAPI DB operations"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# =============================
# DATABASE TABLES
# =============================
def create_db_and_tables():
    """Create database tables on startup"""
    logger.info("Creating database tables...")
    SQLModel.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

# =============================
# CONNECTION TEST
# =============================
def check_db_connection() -> bool:
    """Test database connection"""
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
