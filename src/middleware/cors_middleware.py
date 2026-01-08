from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class CORSMiddlewareAlways:
    """
    Middleware to ensure CORS headers are always present, even in error responses.
    This is applied after other middleware to ensure it runs last.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Store the original send function
        original_send = send

        async def custom_send(message):
            # Only modify response start messages
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                
                # Add CORS headers to every response
                cors_headers = [
                    (b"access-control-allow-origin", b"*"),
                    (b"access-control-allow-credentials", b"true"),
                    (b"access-control-allow-methods", b"*"),
                    (b"access-control-allow-headers", b"*"),
                ]
                
                # Add CORS headers if they don't already exist
                existing_header_names = [header[0].lower() for header in headers]
                for cors_header in cors_headers:
                    if cors_header[0] not in existing_header_names:
                        headers.append(cors_header)
                
                message["headers"] = headers
            
            await original_send(message)

        return await self.app(scope, receive, custom_send)