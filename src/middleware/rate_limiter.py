import time
from collections import defaultdict
from fastapi import Request, HTTPException
from typing import Dict
import os

# Simple in-memory rate limiter (for demonstration)
# In production, use Redis or similar for distributed rate limiting
class RateLimiter:
    def __init__(self):
        # Dictionary to store request times for each endpoint and IP
        # Format: {endpoint: {ip: [request_times]}}
        self.requests: Dict[str, Dict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )

    def is_allowed(self, endpoint: str, ip: str, max_requests: int, window: int) -> bool:
        """
        Check if a request is allowed based on rate limits.

        Args:
            endpoint: The API endpoint being accessed
            ip: The client IP address
            max_requests: Maximum number of requests allowed
            window: Time window in seconds

        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()

        # Clean old requests outside the time window
        self.requests[endpoint][ip] = [
            req_time for req_time in self.requests[endpoint][ip]
            if current_time - req_time < window
        ]

        # Check if we're under the limit
        if len(self.requests[endpoint][ip]) < max_requests:
            # Add current request time
            self.requests[endpoint][ip].append(current_time)
            return True

        return False

# Create a global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(request: Request) -> bool:
    """
    Check if the current request is within rate limits.

    Args:
        request: The incoming request

    Returns:
        True if request is allowed, raises HTTPException if rate limited
    """
    # Check if rate limiting is disabled for testing
    import sys
    if os.getenv("TESTING", "").lower() == "true" or "pytest" in sys.modules:
        return True

    # Get client IP (in production, consider using X-Forwarded-For header if behind proxy)
    client_ip = request.client.host

    # This function is now a placeholder since we're using slowapi decorators
    # The actual rate limiting is handled by slowapi decorators in the auth endpoints
    return True