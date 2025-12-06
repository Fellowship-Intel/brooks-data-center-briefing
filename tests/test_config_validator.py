"""Tests for configuration validator."""
import pytest
import os
from utils.config_validator import ConfigValidator, ConfigError


class TestConfigValidator:
    """Test configuration validation."""
    
    def test_required_var_missing(self):
        """Test validation fails when required var is missing."""
        # Clear GEMINI_API_KEY
        original = os.environ.pop("GEMINI_API_KEY", None)
        try:
            validator = ConfigValidator()
            with pytest.raises(ConfigError):
                validator.validate()
        finally:
            if original:
                os.environ["GEMINI_API_KEY"] = original
    
    def test_validation_success(self):
        """Test successful validation."""
        # Set required var
        os.environ["GEMINI_API_KEY"] = "test_key"
        try:
            validator = ConfigValidator()
            result = validator.validate()
            assert result is True
            config = validator.get_config()
            assert "GEMINI_API_KEY" in config
        finally:
            os.environ.pop("GEMINI_API_KEY", None)
    
    def test_default_values(self):
        """Test default values are set."""
        os.environ["GEMINI_API_KEY"] = "test_key"
        try:
            validator = ConfigValidator()
            validator.validate()
            config = validator.get_config()
            assert config.get("GCP_PROJECT_ID") == "mikebrooks"
            assert config.get("ENVIRONMENT") == "development"
        finally:
            os.environ.pop("GEMINI_API_KEY", None)
    
    def test_sensitive_values_hidden(self):
        """Test sensitive values are hidden in summary."""
        os.environ["GEMINI_API_KEY"] = "secret_key"
        try:
            validator = ConfigValidator()
            validator.validate()
            summary = validator.get_summary(hide_sensitive=True)
            assert summary.get("GEMINI_API_KEY") == "***HIDDEN***"
        finally:
            os.environ.pop("GEMINI_API_KEY", None)

