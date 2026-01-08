from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
from ..config import settings
from contextlib import contextmanager
from typing import Generator
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create the database engine with enhanced configuration
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections after 5 minutes
    pool_size=20,        # Number of connection objects to maintain
    max_overflow=30,     # Additional connections beyond pool_size
    echo=settings.database_echo,  # Enable SQL query logging if configured
)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get DB session for FastAPI endpoints.
    This function is used as a FastAPI dependency to provide database sessions.
    """
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
    """
    Context manager to get DB session for non-FastAPI code.
    This provides a way to get database sessions outside of FastAPI dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_db_and_tables():
    """
    Create database tables based on SQLModel models.
    This function should be called on application startup.
    """
    logger.info("Creating database tables...")
    SQLModel.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_connection():
    """
    Test database connection by attempting to connect and run a simple query.
    Returns True if connection is successful, False otherwise.
    """
    try:
        with get_db_session() as db:
            # Execute a simple query to test the connection
            db.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False