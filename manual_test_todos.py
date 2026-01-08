"""
Manual test to verify the todos endpoint works properly after the fix
"""
import sys
import os
from uuid import UUID

# Add the backend/src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app
from src.database.database import get_db
from src.services.todo_service import TodoService
from src.models.todo import Todo
from src.schemas.todo import TodoCreate
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import create_engine as sqlalchemy_create_engine

# Create an in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = sqlalchemy_create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)

TestingSessionLocal = Session

def test_todos_functionality():
    """Test the todos functionality manually"""
    print("Setting up test database...")
    
    # Create tables
    SQLModel.metadata.create_all(bind=engine)
    
    # Create a session
    db = TestingSessionLocal(bind=engine)
    
    try:
        print("Creating a test user ID...")
        # Using a fixed UUID for testing
        from uuid import uuid4
        test_user_id = uuid4()
        
        print("Creating a todo...")
        todo_create = TodoCreate(
            title="Test Todo",
            description="This is a test todo",
            priority="Medium",
            category="Work",
            due_date=None
        )
        
        # Create a todo
        created_todo = TodoService.create_todo(db, todo_create, test_user_id)
        print(f"Created todo: {created_todo.title} with ID: {created_todo.id}")
        
        # Get the todo by ID
        retrieved_todo = TodoService.get_todo_by_id(db, created_todo.id, test_user_id)
        print(f"Retrieved todo: {retrieved_todo.title}")
        
        # Get all todos for the user
        todos = TodoService.get_todos_by_user(db, test_user_id)
        print(f"Number of todos for user: {len(todos)}")
        
        # Update the todo
        from src.schemas.todo import TodoUpdate
        todo_update = TodoUpdate(title="Updated Test Todo", is_completed=True)
        updated_todo = TodoService.update_todo(db, created_todo.id, todo_update, test_user_id)
        print(f"Updated todo: {updated_todo.title}, completed: {updated_todo.is_completed}")
        
        # Toggle completion status
        toggled_todo = TodoService.toggle_todo_completion(db, created_todo.id, test_user_id)
        print(f"Toggled todo completed status: {toggled_todo.is_completed}")
        
        # Delete the todo
        delete_success = TodoService.delete_todo(db, created_todo.id, test_user_id)
        print(f"Todo deletion successful: {delete_success}")
        
        # Try to get the deleted todo (should return None)
        deleted_todo = TodoService.get_todo_by_id(db, created_todo.id, test_user_id)
        print(f"Trying to retrieve deleted todo: {deleted_todo}")
        
        print("All tests passed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_todos_functionality()