"""
JWT Bearer token authentication for the TaskBox Chatbot Assistant
"""
from fastapi.security import HTTPBearer
from fastapi import Request, HTTPException, status
from typing import Optional
import jwt
from ..config import settings


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials = await super(JWTBearer, self).__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme."
                )

            token = credentials.credentials
            if not self.verify_jwt(token):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token."
                )

            return credentials.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )

    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            # Decode the JWT token
            payload = jwt.decode(jwtoken, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False