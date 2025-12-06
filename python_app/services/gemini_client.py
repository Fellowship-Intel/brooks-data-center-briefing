"""
Shared Gemini AI client utilities.

This module provides unified Gemini API client creation and configuration,
eliminating duplication between gemini_service.py and report_service.py.
"""

import os
import logging
from typing import Optional
import google.generativeai as genai

from config import get_config
from utils.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def initialize_gemini() -> None:
    """
    Initialize the Gemini AI client with API key from config.
    
    Priority:
    1. GCP Secret Manager (production)
    2. Streamlit secrets (Streamlit Cloud)
    3. Environment variables
    4. Centralized config
    
    Raises:
        ConfigurationError: If no API key can be found
    """
    config = get_config()
    
    # Try to get API key from config (which handles Secret Manager)
    api_key = config.gemini_api_key
    
    # Fall back to environment variables if not in config
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
    
    # Try Streamlit secrets if available
    if not api_key:
        try:
            import streamlit as st  # type: ignore
            api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("API_KEY")
        except (ImportError, AttributeError, FileNotFoundError):
            pass
    
    if not api_key:
        raise ConfigurationError(
            "GEMINI_API_KEY not found. Set it via environment variable, "
            "GCP Secret Manager, or Streamlit secrets.",
            missing_keys=["GEMINI_API_KEY"]
        )
    
    genai.configure(api_key=api_key)


def create_gemini_model(
    model_name: Optional[str] = None,
    system_instruction: Optional[str] = None
) -> genai.GenerativeModel:
    """
    Create a configured Gemini model instance.
    
    Args:
        model_name: Model name (defaults to config value)
        system_instruction: Optional system instruction
        
    Returns:
        Configured GenerativeModel instance
    """
    initialize_gemini()
    
    config = get_config()
    if model_name is None:
        model_name = config.gemini_model_name
    
    kwargs = {"model_name": model_name}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction
    
    return genai.GenerativeModel(**kwargs)


# JSON parsing is handled by python_app.utils.json_parser
# Import it here for convenience
from python_app.utils.json_parser import parse_gemini_json_response

