from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import uuid
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.types import String
import sys
from sqlalchemy.types import TypeDecorator
from pydantic import EmailStr


# Use different UUID column type based on the database dialect
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(32) to store stringified UUIDs.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))  # For SQLite

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value) if value else None

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            try:
                return uuid.UUID(value)
            except (ValueError, TypeError):
                return value


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(GUID, primary_key=True))
    email: EmailStr = Field(unique=True, min_length=5, max_length=255)
    password_hash: str = Field(min_length=8, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to Todos
    todos: List["Todo"] = Relationship(back_populates="user")