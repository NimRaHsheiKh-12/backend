from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
import logging
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class SecurityMiddleware:
    """
    Middleware to handle security-related tasks like:
    - Request logging
    - Security headers
    - Basic security checks
    """
    
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        start_time = time.time()

        # Add security headers to response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add security headers
                headers = message.get("headers", [])
                headers.append([b"x-frame-options", b"SAMEORIGIN"])
                headers.append([b"x-content-type-options", b"nosniff"])
                headers.append([b"x-xss-protection", b"1; mode=block"])
                headers.append([b"strict-transport-security", b"max-age=31536000; includeSubDomains"])
                message["headers"] = headers
            await send(message)

        # Process the request
        response = await self.app(scope, receive, send_wrapper)
        
        # Log the request
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {request.client.host} - {process_time:.2f}s")
        
        return response


async def add_security_headers(request: Request, call_next):
    """
    Middleware function to add security headers to responses
    """
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response