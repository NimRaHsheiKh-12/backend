import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add the backend/src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import app
from src.database.database import get_db
from sqlmodel import SQLModel
from src.config import settings
from src.utils.password import hash_password

# Create a test database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_pre_ping=True  # Verify connections before use
)

TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Create the test database tables
SQLModel.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the get_db dependency with our test database
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_client():
    """Provide a test client for API tests"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def authenticated_client(test_client):
    """Provide an authenticated test client"""
    # Register a user
    test_client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    # Login and get token
    login_response = test_client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Add the token to the test client headers
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    
    return test_client

def test_create_todo(authenticated_client):
    """Test creating a todo"""
    response = authenticated_client.post(
        "/todos/",
        json={
            "title": "Test Todo",
            "description": "Test Description",
            "priority": "Medium",
            "category": "Work",
            "due_date": "2023-12-31"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "Test Description"
    assert data["priority"] == "Medium"
    assert data["category"] == "Work"
    assert data["due_date"] == "2023-12-31"
    assert data["is_completed"] is False

def test_get_todos(authenticated_client):
    """Test getting todos"""
    # Create a todo first
    authenticated_client.post(
        "/todos/",
        json={
            "title": "Test Todo",
            "description": "Test Description",
            "priority": "Medium"
        }
    )
    
    response = authenticated_client.get("/todos/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(todo["title"] == "Test Todo" for todo in data)

def test_get_todo_by_id(authenticated_client):
    """Test getting a specific todo by ID"""
    # Create a todo first
    create_response = authenticated_client.post(
        "/todos/",
        json={
            "title": "Test Todo",
            "description": "Test Description",
            "priority": "Medium"
        }
    )
    todo_id = create_response.json()["id"]
    
    response = authenticated_client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Todo"

def test_update_todo(authenticated_client):
    """Test updating a todo"""
    # Create a todo first
    create_response = authenticated_client.post(
        "/todos/",
        json={
            "title": "Test Todo",
            "description": "Test Description",
            "priority": "Medium"
        }
    )
    todo_id = create_response.json()["id"]
    
    response = authenticated_client.put(
        f"/todos/{todo_id}",
        json={
            "title": "Updated Todo",
            "description": "Updated Description",
            "priority": "High",
            "is_completed": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Todo"
    assert data["is_completed"] is True

def test_toggle_todo_completion(authenticated_client):
    """Test toggling todo completion status"""
    # Create a todo first
    create_response = authenticated_client.post(
        "/todos/",
        json={
            "title": "Test Todo",
            "description": "Test Description",
            "priority": "Medium"
        }
    )
    todo_id = create_response.json()["id"]
    
    # Get the initial state
    response = authenticated_client.get(f"/todos/{todo_id}")
    initial_completed = response.json()["is_completed"]
    
    # Toggle the completion status
    response = authenticated_client.patch(f"/todos/{todo_id}/toggle")
    assert response.status_code == 200
    data = response.json()
    # The completion status should be the opposite of the initial state
    assert data["is_completed"] is not initial_completed

def test_delete_todo(authenticated_client):
    """Test deleting a todo"""
    # Create a todo first
    create_response = authenticated_client.post(
        "/todos/",
        json={
            "title": "Test Todo",
            "description": "Test Description",
            "priority": "Medium"
        }
    )
    todo_id = create_response.json()["id"]
    
    response = authenticated_client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204
    
    # Verify the todo is deleted
    response = authenticated_client.get(f"/todos/{todo_id}")
    assert response.status_code == 404