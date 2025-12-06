"""
OAuth utilities for Google Authentication.
Handles OAuth flow creation, authorization URL generation, and token verification.
"""
import os
import json
import logging
from typing import Optional, Dict
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests
from google.oauth2 import id_token

logger = logging.getLogger(__name__)

def get_google_flow(redirect_uri: str) -> Flow:
    """
    Creates a Google OAuth Flow object.
    
    Args:
        redirect_uri: The redirect URI for OAuth callback
        
    Returns:
        Flow object configured for Google OAuth
        
    Raises:
        FileNotFoundError: If client_secret.json not found and env vars not set
        ValueError: If configuration is invalid
    """
    client_secrets_file = ".secrets/client_secret.json"
    
    # Try to load from file first
    if os.path.exists(client_secrets_file):
        flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 
                    'https://www.googleapis.com/auth/userinfo.profile'],
            redirect_uri=redirect_uri
        )
        return flow
    
    # Fallback to environment variables
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise FileNotFoundError(
            "Google OAuth credentials not found. Please provide either:\n"
            "1. .secrets/client_secret.json file, OR\n"
            "2. GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables"
        )
    
    # Create client config from env vars
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'],
        redirect_uri=redirect_uri
    )
    
    return flow


def get_login_url(redirect_uri: str) -> str:
    """
    Generates the Google OAuth authorization URL.
    
    Args:
        redirect_uri: The redirect URI for OAuth callback
        
    Returns:
        Authorization URL string
    """
    try:
        flow = get_google_flow(redirect_uri)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account'
        )
        return authorization_url
    except Exception as e:
        logger.error(f"Error generating login URL: {e}")
        raise


def verify_google_token(token: str) -> Optional[Dict[str, str]]:
    """
    Verifies a Google ID token and returns user information.
    
    Args:
        token: The Google ID token to verify
        
    Returns:
        Dictionary with user info (email, name, sub) if valid, None otherwise
    """
    try:
        # Get client ID from file or env
        client_id = None
        client_secrets_file = ".secrets/client_secret.json"
        
        if os.path.exists(client_secrets_file):
            with open(client_secrets_file, 'r') as f:
                secrets = json.load(f)
                client_id = secrets.get('web', {}).get('client_id')
        else:
            client_id = os.environ.get("GOOGLE_CLIENT_ID")
        
        if not client_id:
            logger.error("Cannot verify token: client_id not found")
            return None
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            client_id
        )
        
        # Extract user information
        user_info = {
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "sub": idinfo.get("sub"),
            "picture": idinfo.get("picture")
        }
        
        return user_info
        
    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None
