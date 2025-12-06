"""Environment configuration validation and management."""
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigValidator:
    """
    Validates and manages application configuration.
    
    Ensures all required environment variables are set and valid.
    """
    
    REQUIRED_VARS = {
        "GEMINI_API_KEY": {
            "description": "Google Gemini API key",
            "required": True,
            "sensitive": True
        },
    }
    
    OPTIONAL_VARS = {
        "GCP_PROJECT_ID": {
            "description": "Google Cloud Project ID",
            "default": "mikebrooks",
            "required": False
        },
        "REPORTS_BUCKET_NAME": {
            "description": "GCS bucket name for reports",
            "default": "mikebrooks-reports",
            "required": False
        },
        "GOOGLE_APPLICATION_CREDENTIALS": {
            "description": "Path to GCP service account JSON",
            "required": False
        },
        "ENVIRONMENT": {
            "description": "Environment name (development, staging, production)",
            "default": "development",
            "required": False
        },
        "SENTRY_DSN": {
            "description": "Sentry DSN for error tracking",
            "required": False,
            "sensitive": True
        },
        "GEMINI_MODEL_NAME": {
            "description": "Gemini model name",
            "default": "gemini-1.5-pro",
            "required": False
        },
        "PORT": {
            "description": "Server port",
            "default": "8080",
            "required": False
        },
        "FLASK_DEBUG": {
            "description": "Flask debug mode",
            "default": "False",
            "required": False
        },
        "ELEVEN_LABS_API_KEY": {
            "description": "Eleven Labs API key for TTS",
            "required": False,
            "sensitive": True
        },
        "ELEVEN_LABS_VOICE_ID": {
            "description": "Eleven Labs voice ID (default: auto-select recommended voice)",
            "required": False
        },
        "TTS_PROVIDER": {
            "description": "TTS provider preference (eleven_labs, gemini, or auto)",
            "default": "eleven_labs",
            "required": False
        },
    }
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.config: Dict[str, Any] = {}
    
    def validate(self) -> bool:
        """
        Validate all configuration.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ConfigError: If validation fails with details
        """
        self.errors = []
        self.warnings = []
        self.config = {}
        
        # Check required variables
        for var_name, var_config in self.REQUIRED_VARS.items():
            value = os.getenv(var_name)
            if not value:
                self.errors.append(
                    f"Required environment variable '{var_name}' is not set. "
                    f"{var_config.get('description', '')}"
                )
            else:
                self.config[var_name] = value
        
        # Check optional variables and set defaults
        for var_name, var_config in self.OPTIONAL_VARS.items():
            value = os.getenv(var_name)
            if not value:
                if "default" in var_config:
                    self.config[var_name] = var_config["default"]
                    logger.info(
                        "Using default value for %s: %s",
                        var_name,
                        var_config["default"]
                    )
                else:
                    self.config[var_name] = None
            else:
                self.config[var_name] = value
        
        # Validate file paths if specified
        creds_path = self.config.get("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path:
            if not Path(creds_path).exists():
                self.warnings.append(
                    f"GOOGLE_APPLICATION_CREDENTIALS path does not exist: {creds_path}"
                )
        
        # Validate environment value
        env = self.config.get("ENVIRONMENT", "development")
        if env not in ["development", "staging", "production"]:
            self.warnings.append(
                f"ENVIRONMENT should be one of: development, staging, production. Got: {env}"
            )
        
        # Check if we have at least one auth method
        if not self.config.get("GEMINI_API_KEY") and not creds_path:
            self.errors.append(
                "Either GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS must be set"
            )
        
        if self.errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in self.errors)
            if self.warnings:
                error_msg += "\n\nWarnings:\n" + "\n".join(f"  - {w}" for w in self.warnings)
            raise ConfigError(error_msg)
        
        if self.warnings:
            logger.warning("Configuration warnings:\n%s", "\n".join(self.warnings))
        
        return True
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get validated configuration dictionary.
        
        Returns:
            Dictionary of configuration values
        """
        return self.config.copy()
    
    def get_summary(self, hide_sensitive: bool = True) -> Dict[str, Any]:
        """
        Get configuration summary (safe for logging).
        
        Args:
            hide_sensitive: Whether to hide sensitive values
            
        Returns:
            Dictionary with configuration summary
        """
        summary = {}
        for key, value in self.config.items():
            if hide_sensitive and self._is_sensitive(key):
                summary[key] = "***HIDDEN***"
            else:
                summary[key] = value
        return summary
    
    def _is_sensitive(self, var_name: str) -> bool:
        """Check if a variable is sensitive."""
        if var_name in self.REQUIRED_VARS:
            return self.REQUIRED_VARS[var_name].get("sensitive", False)
        if var_name in self.OPTIONAL_VARS:
            return self.OPTIONAL_VARS[var_name].get("sensitive", False)
        return False


def validate_config() -> Dict[str, Any]:
    """
    Validate configuration and return config dict.
    
    Returns:
        Validated configuration dictionary
        
    Raises:
        ConfigError: If validation fails
    """
    validator = ConfigValidator()
    validator.validate()
    return validator.get_config()


def get_config_summary() -> Dict[str, Any]:
    """Get safe configuration summary for logging."""
    validator = ConfigValidator()
    try:
        validator.validate()
        return validator.get_summary()
    except ConfigError:
        return {"status": "invalid", "errors": validator.errors}

