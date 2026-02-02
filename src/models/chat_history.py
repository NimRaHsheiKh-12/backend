"""
Chat history model for the TaskBox Chatbot Assistant
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid


class ChatHistory(SQLModel, table=True):
    """
    Model representing chat history in the TaskBox Chatbot Assistant
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True)
    user_message: str
    chatbot_reply: str
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    associated_task_id: uuid.UUID = Field(default=None, foreign_key="todos.id")
    session_id: uuid.UUID = Field(default=None)