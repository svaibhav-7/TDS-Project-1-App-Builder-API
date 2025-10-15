from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.config import settings

security = HTTPBearer()

def verify_secret(secret: str) -> bool:
    """
    Verify if the provided secret matches the expected secret.
    
    Args:
        secret: The secret to verify
        
    Returns:
        bool: True if the secret is valid, False otherwise
    """
    return secret == settings.SECRET_KEY

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get the current user based on the provided credentials.
    
    Args:
        credentials: The HTTP authorization credentials
        
    Returns:
        dict: User information if authenticated
        
    Raises:
        HTTPException: If the credentials are invalid
    """
    if not verify_secret(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": "api_user"}  # In a real app, this would be a user from your database

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    """
    Dependency that makes the user optional.
    
    Args:
        credentials: Optional HTTP authorization credentials
        
    Returns:
        Optional[dict]: User information if authenticated, None otherwise
    """
    if not credentials:
        return None
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
