from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from enum import Enum
from uuid import UUID


class PriorityEnum(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"


# Todo Schemas
class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    priority: PriorityEnum = PriorityEnum.Medium
    category: Optional[str] = None
    due_date: Optional[date] = None


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    priority: Optional[PriorityEnum] = None
    category: Optional[str] = None
    due_date: Optional[date] = None


class TodoResponse(TodoBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}