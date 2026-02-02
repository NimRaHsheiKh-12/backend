"""
Chat request/response schemas for API validation
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class ChatMessageRequest(BaseModel):
    """
    Request schema for processing chat messages
    Only 'message' is required; user_id and current_tasks are optional.
    Authentication is handled via JWT cookies.
    """
    message: str
    user_id: Optional[str] = None
    current_tasks: Optional[List[dict]] = None


class ChatMessageResponse(BaseModel):
    """
    Response schema for processed chat messages
    """
    reply: str
    action_performed: str
    updated_tasks: List[dict]
    success: bool


class ChatHistoryResponse(BaseModel):
    """
    Response schema for chat history
    """
    history: List[dict]
    success: bool


class InitializeSessionRequest(BaseModel):
    """
    Request schema for initializing a chat session
    """
    user_id: str


class InitializeSessionResponse(BaseModel):
    """
    Response schema for initializing a chat session
    """
    session_id: str
    welcome_message: str
    current_tasks_count: int
    success: bool


class EndSessionResponse(BaseModel):
    """
    Response schema for ending a chat session
    """
    message: str
    success: bool