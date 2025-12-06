"""
OAuth2 Utilities for Google Authentication.
Handles flow for both Streamlit (desktop) and FastAPI (web/api).
"""
import os
import logging
import json
from typing import Optional, Dict, List
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
import requests

# Configure logging
logger = logging.getLogger(__name__)

# Constants
GOOGLE_CLIENT_SECRETS_FILE = ".secrets/client_secret.json"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

def get_google_flow(redirect_uri: str) -> Flow:
    """
    Creates a Google OAuth Flow instance.
    """
    # Check if we have the client secret file
    # In production (GCP), this might come from env vars or Secret Manager
    if not os.path.exists(GOOGLE_CLIENT_SECRETS_FILE):
        # Fallback to creating from env vars if file doesn't exist
        client_config = {
            "web": {
                "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        if not client_config["web"]["client_id"] or not client_config["web"]["client_secret"]:
             raise ValueError("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET env vars or client_secret.json file")
             
        return Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
    return Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

def verify_google_token(token: str) -> Optional[Dict[str, str]]:
    """
    Verifies a Google ID token and returns user info.
    """
    try:
        # Verify the token
        # In a real app we'd verify the audience (CLIENT_ID) too
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        id_info = id_token.verify_oauth2_token(token, Request(), client_id)
        
        return {
            "email": id_info.get("email"),
            "name": id_info.get("name"),
            "picture": id_info.get("picture"),
            "sub": id_info.get("sub")
        }
    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        return None

def get_login_url(redirect_uri: str) -> str:
    """
    Generates the Google Login URL.
    """
    flow = get_google_flow(redirect_uri)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    return authorization_url
