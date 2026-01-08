import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from backend.src.config import settings
from backend.src.utils.password import hash_password

# Temporarily override the database URL before importing the main app
import os
original_db_url = os.environ.get("DATABASE_URL")
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from backend.src.main import app
from backend.src.database.database import get_db

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

# Restore the original database URL if it existed
if original_db_url is not None:
    os.environ["DATABASE_URL"] = original_db_url

@pytest.fixture
def test_client():
    """Provide a test client for API tests"""
    with TestClient(app) as client:
        yield client

def test_register_user(test_client):
    """Test user registration endpoint"""
    # Test successful registration
    response = test_client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "test@example.com"
    
    # Test registration with existing email
    response = test_client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 409
    assert "A user with this email already exists" in response.json()["detail"]

def test_login_user(test_client):
    """Test user login endpoint"""
    # First register a user
    test_client.post(
        "/auth/register",
        json={
            "email": "login_test@example.com",
            "password": "testpassword123"
        }
    )
    
    # Test successful login
    response = test_client.post(
        "/auth/login",
        json={
            "email": "login_test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test login with invalid credentials
    response = test_client.post(
        "/auth/login",
        json={
            "email": "login_test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_get_profile(test_client):
    """Test getting user profile"""
    # Register and login a user
    test_client.post(
        "/auth/register",
        json={
            "email": "profile_test@example.com",
            "password": "testpassword123"
        }
    )
    
    login_response = test_client.post(
        "/auth/login",
        json={
            "email": "profile_test@example.com",
            "password": "testpassword123"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Test getting profile with valid token
    response = test_client.get(
        "/auth/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile_test@example.com"
    
    # Test getting profile with invalid token
    response = test_client.get(
        "/auth/profile",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401