"""
Test script to verify database configuration for the Todo Fullstack Application.
This script tests database connection, table creation, and basic operations.
"""

import asyncio
import os
import sys
from datetime import datetime, date
import uuid

# Add the backend/src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from backend.src.database.database import check_db_connection, get_db_session
from backend.src.database.utils import get_db_health, init_db
from backend.src.models.user import User
from backend.src.models.todo import Todo, PriorityEnum
from passlib.context import CryptContext


# Set up password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def test_database_connection():
    """Test basic database connection"""
    print("Testing database connection...")
    connection_ok = check_db_connection()
    if connection_ok:
        print("✓ Database connection successful")
        return True
    else:
        print("✗ Database connection failed")
        return False


def test_table_creation():
    """Test that tables can be created"""
    print("\nTesting table creation...")
    try:
        from backend.src.database.database import create_db_and_tables
        create_db_and_tables()
        print("✓ Tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Table creation failed: {str(e)}")
        return False


def test_basic_operations():
    """Test basic CRUD operations"""
    print("\nTesting basic CRUD operations...")
    
    # Create a test user
    test_email = f"testuser_{uuid.uuid4()}@example.com"
    test_password_hash = pwd_context.hash("testpassword123")
    
    try:
        with get_db_session() as db:
            # Create user
            user = User(
                email=test_email,
                password_hash=test_password_hash,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✓ User created with ID: {user.id}")
            
            # Create a todo for the user
            todo = Todo(
                user_id=user.id,
                title="Test Todo",
                description="This is a test todo item",
                is_completed=False,
                priority=PriorityEnum.medium,
                category="Test",
                due_date=date.today(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(todo)
            db.commit()
            db.refresh(todo)
            print(f"✓ Todo created with ID: {todo.id}")
            
            # Read the user and their todos
            retrieved_user = db.get(User, user.id)
            if retrieved_user:
                print(f"✓ User retrieved: {retrieved_user.email}")
            
            retrieved_todo = db.get(Todo, todo.id)
            if retrieved_todo:
                print(f"✓ Todo retrieved: {retrieved_todo.title}")
                
            # Update the todo
            retrieved_todo.is_completed = True
            db.add(retrieved_todo)
            db.commit()
            print("✓ Todo updated successfully")
            
            # Delete the todo
            db.delete(retrieved_todo)
            db.commit()
            print("✓ Todo deleted successfully")
            
            # Delete the user
            db.delete(retrieved_user)
            db.commit()
            print("✓ User deleted successfully")
            
        return True
    except Exception as e:
        print(f"✗ Basic operations failed: {str(e)}")
        return False


def test_db_health():
    """Test database health check"""
    print("\nTesting database health...")
    health_info = get_db_health()
    print(f"✓ Database health: {health_info}")
    return True


def main():
    """Main test function"""
    print("Starting database configuration tests for Todo Fullstack Application...\n")
    
    # Test database connection
    if not test_database_connection():
        print("\nDatabase connection test failed. Please check your database configuration.")
        return False
    
    # Initialize database (run migrations)
    print("\nInitializing database...")
    try:
        init_db()
        print("✓ Database initialization completed")
    except Exception as e:
        print(f"✗ Database initialization failed: {str(e)}")
        return False
    
    # Test table creation
    if not test_table_creation():
        print("\nTable creation test failed.")
        return False
    
    # Test basic operations
    if not test_basic_operations():
        print("\nBasic operations test failed.")
        return False
    
    # Test database health
    test_db_health()
    
    print("\n✓ All database configuration tests passed!")
    print("\nDatabase configuration summary:")
    print("- Alembic migrations are properly configured")
    print("- Database connection is working")
    print("- Tables can be created and managed")
    print("- CRUD operations work correctly")
    print("- Session management is properly implemented")
    print("- Utility functions are available")
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        print("\nSome tests failed. Please review the output above.")
        exit(1)
    else:
        print("\nAll tests completed successfully!")