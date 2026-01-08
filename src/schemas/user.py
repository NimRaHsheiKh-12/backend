from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

# User Registration Schema
class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!"
            }
        }
    }

# User Registration Response Schema
class UserRegistrationResponse(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}

# User Login Schema
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!"
            }
        }
    }

# User Response Schema (without sensitive data)
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}

# Token Response Schema
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    }

# Token Data Schema
class TokenData(BaseModel):
    email: Optional[str] = None