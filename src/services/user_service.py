from typing import Optional
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from ..models.user import User
from ..schemas.user import UserRegistrationRequest, UserLoginRequest
from ..utils.password import hash_password, verify_password
from fastapi import HTTPException, status
from uuid import UUID


class UserService:
    @staticmethod
    def create_user(db: Session, user_data: UserRegistrationRequest):
        """
        Create a new user with the provided registration data.

        Args:
            db: Database session
            user_data: Registration request data

        Returns:
            Created User object
        """
        # Hash the password
        hashed_password = hash_password(user_data.password)

        # Normalize the email by stripping whitespace and converting to lowercase
        normalized_email = user_data.email.strip().lower()

        # Create the user object
        db_user = User(
            email=normalized_email,
            password_hash=hashed_password
        )

        # Add to database
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        except IntegrityError:
            # Rollback the transaction
            db.rollback()
            # Check if the user already exists (might happen due to race condition)
            existing_user = UserService.get_user_by_email(db, normalized_email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists"
                )
            else:
                # If the user doesn't exist but we still got an integrity error, re-raise
                raise

        # Convert the user object to a response model to ensure proper serialization
        from ..schemas.user import UserRegistrationResponse
        # Create response object with proper string conversion of UUID
        # Handle cases where created_at might be None (e.g., in tests with mock objects)
        created_at = db_user.created_at
        if created_at is None:
            from datetime import datetime
            created_at = datetime.utcnow()
        return UserRegistrationResponse(
            id=str(db_user.id),
            email=db_user.email,
            created_at=created_at
        )

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get a user by their email address.

        Args:
            db: Database session
            email: Email address to search for

        Returns:
            User object if found, None otherwise
        """
        # Normalize the email by stripping whitespace and converting to lowercase
        normalized_email = email.strip().lower()
        statement = select(User).where(func.lower(func.trim(User.email)) == normalized_email)
        result = db.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        """
        Authenticate a user by email and password.

        Args:
            db: Database session
            email: User's email address
            password: User's plain text password

        Returns:
            User object if credentials are valid, None otherwise
        """
        # Normalize the email by stripping whitespace and converting to lowercase
        normalized_email = email.strip().lower()
        user = UserService.get_user_by_email(db, normalized_email)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        # Return the user object as a response model to ensure proper serialization
        from ..schemas.user import UserResponse
        # Create response object with proper string conversion of UUID
        # Handle cases where created_at might be None (e.g., in tests with mock objects)
        created_at = user.created_at
        if created_at is None:
            from datetime import datetime
            created_at = datetime.utcnow()
        return UserResponse(
            id=str(user.id),
            email=user.email,
            created_at=created_at
        )