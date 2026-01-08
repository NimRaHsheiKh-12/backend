"""
Database utility functions for the Todo Fullstack Application.
This module contains utility functions for database operations,
connection management, and migration handling.
"""

from typing import Optional
from sqlalchemy import text
from .database import engine, get_db_session
from backend.src.models.user import User
from backend.src.models.todo import Todo
import logging

logger = logging.getLogger(__name__)


def run_migrations():
    """
    Run pending database migrations.
    This function can be called to apply any pending migrations to the database.
    """
    try:
        # Import alembic functionality
        from alembic.config import Config
        from alembic import command
        import os
        
        # Get the directory containing this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate to the backend directory to find alembic.ini
        backend_dir = os.path.dirname(os.path.dirname(current_dir))
        alembic_cfg_path = os.path.join(backend_dir, "alembic.ini")
        
        alembic_cfg = Config(alembic_cfg_path)
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migrations applied successfully")
    except ImportError:
        logger.warning("Alembic not available, skipping migrations")
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        raise


def get_db_health() -> dict:
    """
    Get database health information.
    Returns a dictionary with database status and statistics.
    """
    health_info = {
        "status": "unhealthy",
        "tables": {
            "users": 0,
            "todos": 0
        },
        "connection_test": False
    }
    
    try:
        # Test basic connection
        with get_db_session() as db:
            # Test connection
            result = db.execute(text("SELECT 1"))
            health_info["connection_test"] = True
            
            # Count records in each table
            user_count = db.query(User).count()
            todo_count = db.query(Todo).count()
            
            health_info["tables"]["users"] = user_count
            health_info["tables"]["todos"] = todo_count
            health_info["status"] = "healthy"
            
    except Exception as e:
        logger.error(f"Error checking database health: {str(e)}")
        health_info["error"] = str(e)
    
    return health_info


def init_db():
    """
    Initialize the database with required setup.
    This function runs migrations and performs any other required initialization.
    """
    logger.info("Initializing database...")
    
    # Run migrations
    run_migrations()
    
    # Additional initialization can be added here
    logger.info("Database initialization completed")


def get_engine():
    """
    Get the database engine instance.
    Useful for direct access to the engine when needed.
    """
    return engine


def reset_db():
    """
    Reset the database by dropping and recreating all tables.
    WARNING: This will delete all data in the database.
    """
    logger.warning("Resetting database - all data will be lost!")
    
    # Import all models to ensure they're registered with SQLModel metadata
    from sqlmodel import SQLModel
    
    # Drop all tables
    SQLModel.metadata.drop_all(bind=engine)
    
    # Recreate all tables
    SQLModel.metadata.create_all(bind=engine)
    
    logger.info("Database reset completed")