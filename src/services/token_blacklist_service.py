from sqlmodel import Session, select
from ..models.token_blacklist import TokenBlacklist
from datetime import datetime
from jose import jwt
from ..config import settings


class TokenBlacklistService:
    @staticmethod
    def blacklist_token(db: Session, token: str, expires_at: datetime):
        """
        Add a token to the blacklist to invalidate it.

        Args:
            db: Database session
            token: JWT token to blacklist
            expires_at: When the token would have naturally expired
        """
        # Check if token is already blacklisted
        existing_blacklist = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
        if existing_blacklist:
            return  # Token is already blacklisted

        # Create a new blacklist entry
        blacklist_entry = TokenBlacklist(
            token=token,
            expires_at=expires_at
        )
        
        db.add(blacklist_entry)
        db.commit()

    @staticmethod
    def is_token_blacklisted(db: Session, token: str) -> bool:
        """
        Check if a token is in the blacklist.

        Args:
            db: Database session
            token: JWT token to check

        Returns:
            True if token is blacklisted, False otherwise
        """
        # First, try to decode the token to get its expiration time
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"verify_signature": False}  # We just need to read the payload
            )
            exp = payload.get("exp")
            if exp:
                # Check if the token is in the blacklist and hasn't expired yet
                statement = select(TokenBlacklist).where(
                    TokenBlacklist.token == token,
                    TokenBlacklist.expires_at > datetime.utcnow()
                )
                result = db.execute(statement)
                return result.scalar_one_or_none() is not None
        except jwt.JWTError:
            # If we can't decode the token, it's invalid anyway
            return True

        return False

    @staticmethod
    def cleanup_expired_tokens(db: Session):
        """
        Remove expired tokens from the blacklist.

        Args:
            db: Database session
        """
        from datetime import datetime
        expired_tokens = db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at <= datetime.utcnow()
        ).all()
        
        for token in expired_tokens:
            db.delete(token)
        
        db.commit()