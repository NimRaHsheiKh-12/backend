"""
Tests for the TaskBox Chatbot Assistant functionality
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from sqlmodel import Session

from backend.src.main import app
from backend.src.models.todo import Todo
from backend.src.models.user import User


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_process_chat_add_task(client):
    """Test adding a task via chat message"""
    # Mock user authentication
    with patch("backend.src.api.chat.JWTBearer.__call__") as mock_jwt:
        mock_jwt.return_value = "mocked_token"
        
        # Prepare test data
        request_data = {
            "user_id": "test_user_123",
            "message": "Add 'Buy groceries' to my list",
            "current_tasks": []
        }
        
        # Call the endpoint
        response = client.post("/chat/process", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "Buy groceries" in response_data["reply"]
        assert len(response_data["updated_tasks"]) == 1
        assert response_data["updated_tasks"][0]["title"] == "Buy groceries"
        assert response_data["action_performed"] == "CREATE"


@pytest.mark.asyncio
async def test_process_chat_view_tasks(client):
    """Test viewing tasks via chat message"""
    # Mock user authentication
    with patch("backend.src.api.chat.JWTBearer.__call__") as mock_jwt:
        mock_jwt.return_value = "mocked_token"
        
        # Prepare test data with existing tasks
        current_tasks = [
            {
                "id": "task1",
                "user_id": "test_user_123",
                "title": "Buy groceries",
                "description": "",
                "is_completed": False,
                "priority": "Medium",
                "category": "Personal",
                "due_date": None,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
        
        request_data = {
            "user_id": "test_user_123",
            "message": "Show my tasks",
            "current_tasks": current_tasks
        }
        
        # Call the endpoint
        response = client.post("/chat/process", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "Buy groceries" in response_data["reply"]
        assert response_data["action_performed"] == "READ"


@pytest.mark.asyncio
async def test_process_chat_complete_task(client):
    """Test completing a task via chat message"""
    # Mock user authentication
    with patch("backend.src.api.chat.JWTBearer.__call__") as mock_jwt:
        mock_jwt.return_value = "mocked_token"
        
        # Prepare test data with existing tasks
        current_tasks = [
            {
                "id": "task1",
                "user_id": "test_user_123",
                "title": "Buy groceries",
                "description": "",
                "is_completed": False,
                "priority": "Medium",
                "category": "Personal",
                "due_date": None,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
        
        request_data = {
            "user_id": "test_user_123",
            "message": "Mark 'Buy groceries' as completed",
            "current_tasks": current_tasks
        }
        
        # Call the endpoint
        response = client.post("/chat/process", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "Buy groceries" in response_data["reply"]
        assert response_data["action_performed"] == "COMPLETE"
        assert response_data["updated_tasks"][0]["is_completed"] is True


@pytest.mark.asyncio
async def test_process_chat_invalid_message(client):
    """Test handling invalid chat message"""
    # Mock user authentication
    with patch("backend.src.api.chat.JWTBearer.__call__") as mock_jwt:
        mock_jwt.return_value = "mocked_token"
        
        # Prepare test data
        request_data = {
            "user_id": "test_user_123",
            "message": "This is not a valid task command",
            "current_tasks": []
        }
        
        # Call the endpoint
        response = client.post("/chat/process", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["action_performed"] == "NONE"


def test_get_chat_history(client):
    """Test retrieving chat history for a user"""
    # Mock user authentication
    with patch("backend.src.api.chat.JWTBearer.__call__") as mock_jwt:
        mock_jwt.return_value = "mocked_token"
        
        # Call the endpoint
        response = client.get("/chat/history/test_user_123")
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "history" in response_data


@pytest.mark.asyncio
async def test_initialize_chat_session(client):
    """Test initializing a chat session"""
    # Mock user authentication
    with patch("backend.src.api.chat.JWTBearer.__call__") as mock_jwt:
        mock_jwt.return_value = "mocked_token"
        
        # Prepare test data
        request_data = {
            "user_id": "test_user_123"
        }
        
        # Call the endpoint
        response = client.post("/chat/session", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "session_id" in response_data
        assert "welcome_message" in response_data


def test_end_chat_session(client):
    """Test ending a chat session"""
    # Mock user authentication
    with patch("backend.src.api.chat.JWTBearer.__call__") as mock_jwt:
        mock_jwt.return_value = "mocked_token"
        
        # Call the endpoint
        response = client.delete("/chat/session/test_session_123")
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True