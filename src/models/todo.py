from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, date
import uuid
from enum import Enum
from sqlalchemy import Column, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from .user import GUID  # Import GUID from user model for consistency


if TYPE_CHECKING:
    from .user import User


class PriorityEnum(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"


class Todo(SQLModel, table=True):
    __tablename__ = "todos"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(GUID, primary_key=True))
    user_id: uuid.UUID = Field(sa_column=Column(GUID, ForeignKey("users.id"), nullable=False))
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_completed: bool = Field(default=False)
    priority: PriorityEnum = Field(default=PriorityEnum.Medium)
    category: Optional[str] = Field(default=None, max_length=50)
    due_date: Optional[date] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to User
    user: "User" = Relationship(back_populates="todos")

    # Add check constraint for priority
    __table_args__ = (
        CheckConstraint(
            "priority IN ('Low', 'Medium', 'High')",
            name="valid_priority_values"
        ),
    )