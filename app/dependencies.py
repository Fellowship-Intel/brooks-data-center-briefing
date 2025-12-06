"""
FastAPI Dependencies.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any
from utils.oauth import verify_google_token
import os

# We use the tokenUrl parameter just for OpenAPI docs, but we don't host a token endpoint
# Clients (Streamlit/Frontend) should get token from Google directly
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Validates Google ID token and returns user info.
    If no token provided (and environment is dev), allows bypass if configured.
    """
    if not token:
        # Check dev mode bypass
        if os.environ.get("ENVIRONMENT") == "development" and os.environ.get("ENABLE_AUTH_BYPASS") == "true":
             return {"email": "dev@example.com", "name": "Dev User"}
             
        # If no token and not dev bypass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = verify_google_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
