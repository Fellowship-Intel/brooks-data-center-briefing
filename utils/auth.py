"""Authentication and authorization utilities."""
import logging
import hashlib
import secrets
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Simple authentication manager for multi-client support.
    
    In production, you'd want to use a proper auth system (OAuth, JWT, etc.).
    This is a basic implementation for demonstration.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # In production, store this in a database
        self.client_credentials: Dict[str, str] = {}
    
    def create_session(self, client_id: str) -> str:
        """
        Create a new session for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Session token
        """
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            "client_id": client_id,
            "created_at": None  # Could add timestamp
        }
        logger.info("Created session for client: %s", client_id)
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[str]:
        """
        Validate session token and return client_id.
        
        Args:
            session_token: Session token
            
        Returns:
            Client ID if valid, None otherwise
        """
        session = self.sessions.get(session_token)
        if session:
            return session.get("client_id")
        return None
    
    def revoke_session(self, session_token: str) -> bool:
        """Revoke a session."""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False


# Global auth manager
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get or create global auth manager."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def get_current_client_id() -> str:
    """
    Get current client ID from environment or default.
    
    In a real app, this would come from the authenticated session.
    """
    return os.getenv("CLIENT_ID", "michael_brooks")


def require_client_access(client_id: str, requested_client_id: str) -> bool:
    """
    Check if current client has access to requested client's data.
    
    Args:
        client_id: Current authenticated client ID
        requested_client_id: Requested client ID
        
    Returns:
        True if access is allowed, False otherwise
    """
    # For now, clients can only access their own data
    # In the future, you could add admin roles, etc.
    return client_id == requested_client_id

