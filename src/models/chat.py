"""
Chat message model for the TaskBox Chatbot Assistant
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid


class ChatMessage(SQLModel, table=True):
    """
    Model representing a chat message in the TaskBox Chatbot Assistant
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True)
    user_message: str
    chatbot_reply: str
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    associated_task_id: uuid.UUID = Field(default=None)
    session_id: uuid.UUID = Field(default=None)