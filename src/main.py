from fastapi import FastAPI
from .config import settings
from .middleware.error_handler import http_exception_handler, general_exception_handler
from .api import auth
from .api import todo
from .api import chat
from fastapi.middleware.cors import CORSMiddleware
from .middleware.rate_limiter import check_rate_limit
from fastapi import Request
from .database.database import create_db_and_tables
from .utils.logging import logger, log_security_event
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator


# Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    description="API for Todo Fullstack Application",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize app on startup"""
    try:
        create_db_and_tables()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Application shutting down")

# Add CORS middleware - this should be one of the first middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add rate limiting middleware - but skip it for preflight requests
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for preflight requests
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    # Apply rate limiting to auth endpoints
    if request.url.path.startswith("/auth"):
        check_rate_limit(request)

    response = await call_next(request)
    return response

# Add request logging middleware - but skip it for preflight requests to avoid unnecessary logs
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Skip logging for preflight requests to reduce noise
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Log the request
    logger.info(f"{request.method} {request.url.path} - {request.client.host} - {process_time:.2f}s - {response.status_code}")

    # Log security events for auth endpoints
    if request.url.path.startswith("/auth"):
        log_security_event(
            event_type="auth_request",
            ip_address=request.client.host,
            details={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )

    return response

# Register exception handlers
app.add_exception_handler(401, http_exception_handler)  # Add handler for 401 Unauthorized
app.add_exception_handler(404, http_exception_handler)
app.add_exception_handler(405, http_exception_handler)  # Add handler for 405 Method Not Allowed
app.add_exception_handler(500, general_exception_handler)

# Include API routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(todo.router, prefix="/todos", tags=["todos"])
app.include_router(chat.router, tags=["chat"])  # No prefix since the router already has it

@app.get("/")
def read_root():
    return {"message": "Welcome to Todo Fullstack App API"}

