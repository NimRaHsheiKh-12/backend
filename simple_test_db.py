"""
Simple test script to verify database configuration for the Todo Fullstack Application.
This script tests database connection, table creation, and basic operations.
"""

import sys
import os
# Add the backend/src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from sqlmodel import SQLModel, Session
from backend.src.config import settings
from backend.src.models.user import User
from backend.src.models.todo import Todo, PriorityEnum
from datetime import datetime, date
import uuid
from passlib.context import CryptContext

# Set up password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_database_connection():
    """Test basic database connection"""
    print("Testing database connection...")
    try:
        engine = create_engine(settings.database_url)
        with Session(engine) as session:
            result = session.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        return False

def test_table_creation():
    """Test that tables can be created"""
    print("\nTesting table creation...")
    try:
        engine = create_engine(settings.database_url)
        # Create all tables based on SQLModel models
        SQLModel.metadata.create_all(engine)
        print("✓ Tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Table creation failed: {str(e)}")
        return False

def test_basic_operations():
    """Test basic CRUD operations"""
    print("\nTesting basic CRUD operations...")
    
    engine = create_engine(settings.database_url)
    
    # Create a test user
    test_email = f"testuser_{uuid.uuid4()}@example.com"
    test_password_hash = pwd_context.hash("testpassword123")
    
    try:
        with Session(engine) as session:
            # Create user
            user = User(
                email=test_email,
                password_hash=test_password_hash,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(user)
            session.commit()
            session.refresh(user)
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
            session.add(todo)
            session.commit()
            session.refresh(todo)
            print(f"✓ Todo created with ID: {todo.id}")
            
            # Read the user and their todos
            retrieved_user = session.get(User, user.id)
            if retrieved_user:
                print(f"✓ User retrieved: {retrieved_user.email}")
            
            retrieved_todo = session.get(Todo, todo.id)
            if retrieved_todo:
                print(f"✓ Todo retrieved: {retrieved_todo.title}")
                
            # Update the todo
            retrieved_todo.is_completed = True
            session.add(retrieved_todo)
            session.commit()
            print("✓ Todo updated successfully")
            
            # Delete the todo
            session.delete(retrieved_todo)
            session.commit()
            print("✓ Todo deleted successfully")
            
            # Delete the user
            session.delete(retrieved_user)
            session.commit()
            print("✓ User deleted successfully")
            
        return True
    except Exception as e:
        print(f"✗ Basic operations failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("Starting database configuration tests for Todo Fullstack Application...\n")
    
    # Test database connection
    if not test_database_connection():
        print("\nDatabase connection test failed. Please check your database configuration.")
        return False
    
    # Test table creation
    if not test_table_creation():
        print("\nTable creation test failed.")
        return False
    
    # Test basic operations
    if not test_basic_operations():
        print("\nBasic operations test failed.")
        return False
    
    print("\n✓ All database configuration tests passed!")
    print("\nDatabase configuration summary:")
    print("- Database connection is working")
    print("- Tables can be created and managed")
    print("- CRUD operations work correctly")
    print("- Models are properly defined")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\nSome tests failed. Please review the output above.")
        exit(1)
    else:
        print("\nAll tests completed successfully!")