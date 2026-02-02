"""
Utility package initializer for `utils`.

Avoid importing submodules eagerly to prevent import-time errors
when `utils` is loaded outside of the full package context (for
example, when running small scripts that import a single util).

Import submodules lazily or fall back gracefully if dependencies
aren't available at import time.
"""

__all__ = []

# Import safe helpers if available, but don't fail the whole package
# import when optional parts can't be loaded in some contexts.
try:
    from .password import hash_password, verify_password
    __all__.extend(["hash_password", "verify_password"])
except Exception:
    hash_password = None
    verify_password = None

try:
    from .token import create_access_token, verify_token
    __all__.extend(["create_access_token", "verify_token"])
except Exception:
    create_access_token = None
    verify_token = None

try:
    from .logging import logger, log_security_event
    __all__.extend(["logger", "log_security_event"])
except Exception:
    logger = None
    log_security_event = None