from passlib.context import CryptContext

# Create a password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password to hash
    
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    """
    Verify a plain text password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password to compare against
    
    Returns:
        True if password matches the hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)