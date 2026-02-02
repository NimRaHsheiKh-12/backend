"""
Chat session model for the TaskBox Chatbot Assistant
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid
from typing import Dict, Any
from sqlalchemy import JSON


class ChatSession(SQLModel, table=True):
    """
    Model representing a chat session in the TaskBox Chatbot Assistant
    """
    session_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True)
    started_at: datetime = Field(default_factory=datetime.now)
    last_interaction_at: datetime = Field(default_factory=datetime.now)
    context_data: Dict[str, Any] = Field(default={}, sa_type=JSON)  # Store conversation context as JSON
    is_active: bool = Field(default=True)