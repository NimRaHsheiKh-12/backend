import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from ..config import settings


def setup_logging():
    """
    Set up comprehensive logging configuration for the application
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create a custom formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create a rotating file handler for general logs
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO if not settings.debug else logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Create a separate handler for security-related logs
    security_handler = RotatingFileHandler(
        "logs/security.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(formatter)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if not settings.debug else logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(security_handler)
    
    # Also log to stdout if in debug mode
    if settings.debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Set specific log levels for different modules
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )
    
    return root_logger


def log_security_event(event_type: str, user_id: str = None, ip_address: str = None, details: dict = None):
    """
    Log a security-related event
    
    Args:
        event_type: Type of security event (e.g., "login_attempt", "failed_auth", "suspicious_activity")
        user_id: ID of the user involved in the event
        ip_address: IP address of the request
        details: Additional details about the event
    """
    security_logger = logging.getLogger("security")
    event_data = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    security_logger.info(f"SECURITY_EVENT: {event_data}")


# Initialize logging when module is imported
logger = setup_logging()

# Create a specific logger for security events
security_logger = logging.getLogger("security")