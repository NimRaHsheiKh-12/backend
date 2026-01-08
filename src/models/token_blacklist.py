from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.types import String
import sys
from sqlalchemy.types import TypeDecorator


# Use the same GUID class as in the user model for consistency
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


class TokenBlacklist(SQLModel, table=True):
    __tablename__ = "token_blacklist"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(GUID, primary_key=True))
    token: str = Field(unique=True, max_length=1000)  # Store the JWT token
    blacklisted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field()  # When the token would have naturally expired