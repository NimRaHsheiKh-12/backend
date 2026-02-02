from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..schemas.user import UserRegistrationRequest, UserRegistrationResponse, UserLoginRequest, TokenResponse, UserResponse
from ..services.user_service import UserService
from ..utils.token import create_access_token, verify_token
from datetime import timedelta, datetime
from ..config import settings
from ..auth.auth_handler import get_current_user
from ..models.user import User
from ..services.token_blacklist_service import TokenBlacklistService
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_auth_register)  # Limit registration based on config
async def register_user(request: Request, user_data: UserRegistrationRequest, db: Session = Depends(get_db)):
    """
    Register a new user with email and password.
    """
    # Validate password complexity
    if len(user_data.password) < settings.password_min_length:
        raise HTTPException(
            status_code=status.HTTP_400,
            detail=f"Password must be at least {settings.password_min_length} characters long"
        )

    # Check if user with this email already exists
    existing_user = UserService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )

    # Additional validation can be added here if needed
    # For example, password complexity checks could be implemented

    try:
        # Create the new user
        user = UserService.create_user(db, user_data)
    except Exception as e:
        # Log the error and return a generic message to avoid exposing system details
        from ..utils.logging import logger
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to an internal server error"
        )

    # Return the created user data
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_auth_login)  # Limit login based on config
async def login_user(request: Request, user_data: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    try:
        # Authenticate the user
        user = UserService.authenticate_user(db, user_data.email, user_data.password)
        if not user:
            # Log failed login attempt for security monitoring
            from ..utils.logging import logger
            logger.warning(f"Failed login attempt for email: {user_data.email} from IP: {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )

        # Log successful login for security monitoring
        from ..utils.logging import logger
        logger.info(f"Successful login for user: {user_data.email} from IP: {request.client.host}")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        # Log the error and return a generic message to avoid exposing system details
        from ..utils.logging import logger
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to an internal server error"
        )


@router.post("/logout")
@limiter.limit(settings.rate_limit_auth_logout)  # Limit logout based on config
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by adding their token to the blacklist.
    """
    try:
        # Get the authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing or invalid",
            )

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Decode the token to get its expiration time
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"verify_signature": False}  # We just need to read the payload
            )
            exp = payload.get("exp")
            if exp:
                expires_at = datetime.utcfromtimestamp(exp)
            else:
                # Default to current time + 15 minutes if no exp found
                expires_at = datetime.utcnow() + timedelta(minutes=15)
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_400,
                detail="Invalid token"
            )

        # Add token to blacklist
        TokenBlacklistService.blacklist_token(db, token, expires_at)

        # Log successful logout for security monitoring
        from ..utils.logging import logger
        logger.info(f"Successful logout for user: {current_user.email} from IP: {request.client.host}")

        return {"message": "Successfully logged out"}

    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        # Log the error and return a generic message to avoid exposing system details
        from ..utils.logging import logger
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed due to an internal server error"
        )


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get authenticated user's profile information.
    """
    try:
        # Convert the user model to a response model to ensure proper serialization
        return UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            created_at=current_user.created_at
        )
    except Exception as e:
        # Log the error and return a generic message to avoid exposing system details
        from ..utils.logging import logger
        logger.error(f"Profile retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile retrieval failed due to an internal server error"
        )


# Schema for token validation response
from pydantic import BaseModel

class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "valid": True,
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
            }
        }
    }


@router.post("/validate-token", response_model=TokenValidationResponse)
@limiter.limit(settings.rate_limit_auth_validate_token)  # Limit token validation based on config
async def validate_token(request: Request, current_user: User = Depends(get_current_user)):
    """
    Validate JWT token without returning user data.
    """
    try:
        return TokenValidationResponse(
            valid=True,
            user_id=str(current_user.id)
        )
    except Exception as e:
        # Log the error and return a generic message to avoid exposing system details
        from ..utils.logging import logger
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation failed due to an internal server error"
        )