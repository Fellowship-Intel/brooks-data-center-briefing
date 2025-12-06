"""
Centralized application configuration.

This module provides a single source of truth for all application configuration,
replacing hardcoded values throughout the codebase.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field

# Try to load from GCP Secret Manager if available
try:
    from gcp_clients import access_secret_value, get_project_id as _get_gcp_project_id
    _SECRET_MANAGER_AVAILABLE = True
except ImportError:
    _SECRET_MANAGER_AVAILABLE = False
    def access_secret_value(*args, **kwargs): return None
    def _get_gcp_project_id(): return None

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """
    Application configuration with environment variable support and GCP Secret Manager fallback.
    
    All configuration values can be overridden via environment variables.
    Sensitive values (API keys) are loaded from GCP Secret Manager in production.
    """
    
    # GCP Configuration
    gcp_project_id: str = field(default_factory=lambda: os.getenv("GCP_PROJECT_ID", "mikebrooks"))
    reports_bucket_name: str = field(default_factory=lambda: os.getenv("REPORTS_BUCKET_NAME", "mikebrooks-reports"))
    google_application_credentials: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    
    # Client Configuration
    default_client_id: str = field(default_factory=lambda: os.getenv("DEFAULT_CLIENT_ID", "michael_brooks"))
    default_watchlist: list[str] = field(default_factory=lambda: [
        ticker.strip() 
        for ticker in os.getenv("DEFAULT_WATCHLIST", "IREN,CRWV,NBIS,MRVL").split(",")
        if ticker.strip()
    ])
    
    # API Keys (loaded from Secret Manager in production, env vars in dev)
    gemini_api_key: Optional[str] = None
    eleven_labs_api_key: Optional[str] = None
    eleven_labs_voice_id: Optional[str] = field(default_factory=lambda: os.getenv("ELEVEN_LABS_VOICE_ID"))
    
    # Model Configuration
    gemini_model_name: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-exp"))
    gemini_tts_model: str = field(default_factory=lambda: os.getenv("GEMINI_TTS_MODEL", "gemini-1.5-flash"))
    
    # TTS Configuration
    tts_provider: str = field(default_factory=lambda: os.getenv("TTS_PROVIDER", "eleven_labs"))
    
    # Server Configuration
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8080")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    
    # Monitoring
    sentry_dsn: Optional[str] = field(default_factory=lambda: os.getenv("SENTRY_DSN"))
    
    # Cache Configuration
    cache_ttl_hours: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_HOURS", "24")))
    
    # Rate Limiting
    rate_limit_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")))
    
    def __post_init__(self):
        """Load sensitive values from Secret Manager if available."""
        # Try to load from Secret Manager first (production)
        if _SECRET_MANAGER_AVAILABLE and self.environment == "production":
            try:
                project_id = _get_gcp_project_id() or self.gcp_project_id
                
                if not self.gemini_api_key:
                    try:
                        self.gemini_api_key = access_secret_value("GEMINI_API_KEY", project_id=project_id)
                    except Exception as e:
                        logger.debug("Could not load GEMINI_API_KEY from Secret Manager: %s", e)
                
                if not self.eleven_labs_api_key:
                    try:
                        self.eleven_labs_api_key = access_secret_value("ELEVEN_LABS_API_KEY", project_id=project_id)
                    except Exception as e:
                        logger.debug("Could not load ELEVEN_LABS_API_KEY from Secret Manager: %s", e)
            except Exception as e:
                logger.warning("Could not access Secret Manager, falling back to environment variables: %s", e)
        
        # Fall back to environment variables
        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
        
        if not self.eleven_labs_api_key:
            self.eleven_labs_api_key = os.getenv("ELEVEN_LABS_API_KEY")
        
        # Try Streamlit secrets if available (for Streamlit Cloud)
        if not self.gemini_api_key:
            try:
                import streamlit as st
                self.gemini_api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("API_KEY")
            except (ImportError, AttributeError, FileNotFoundError):
                pass
        
        # Validate required values
        if not self.gemini_api_key:
            logger.warning(
                "GEMINI_API_KEY not found. Set it via environment variable, "
                "GCP Secret Manager, or Streamlit secrets."
            )
    
    def to_dict(self, hide_sensitive: bool = True) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Args:
            hide_sensitive: If True, hide sensitive values (API keys)
            
        Returns:
            Configuration dictionary
        """
        data = {
            "gcp_project_id": self.gcp_project_id,
            "reports_bucket_name": self.reports_bucket_name,
            "default_client_id": self.default_client_id,
            "default_watchlist": self.default_watchlist,
            "gemini_model_name": self.gemini_model_name,
            "gemini_tts_model": self.gemini_tts_model,
            "tts_provider": self.tts_provider,
            "port": self.port,
            "environment": self.environment,
            "cache_ttl_hours": self.cache_ttl_hours,
            "rate_limit_per_minute": self.rate_limit_per_minute,
        }
        
        if not hide_sensitive:
            data["gemini_api_key"] = "***" if self.gemini_api_key else None
            data["eleven_labs_api_key"] = "***" if self.eleven_labs_api_key else None
            data["eleven_labs_voice_id"] = self.eleven_labs_voice_id
        
        return data


# Global configuration instance (lazy-loaded singleton)
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the global application configuration instance.
    
    Returns:
        AppConfig instance (singleton)
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config_instance
    _config_instance = None

