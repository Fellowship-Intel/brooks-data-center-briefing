import streamlit as st
import logging
import os
import sys
from pathlib import Path
from config import get_config

def init_app():
    """Initialize the application: logging, credentials, config, and Streamlit page."""
    
    # helper to find root dir
    # this file is in python_app/utils/setup.py
    # root is up 3 levels
    root_dir = Path(__file__).resolve().parent.parent.parent
    
    # 1. Logging Setup
    # Only configure if not already configured to avoid duplicate handlers on reload
    logger = logging.getLogger("root")
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
            force=True
        )

    # 2. GCP Credentials Auto-setup
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        default_creds_path = root_dir / ".secrets" / "app-backend-sa.json"
        if default_creds_path.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(default_creds_path)
            logging.info(f"Loaded credentials from {default_creds_path}")

    # 3. Project ID default
    config = get_config()
    if not os.getenv("GCP_PROJECT_ID"):
        os.environ["GCP_PROJECT_ID"] = config.gcp_project_id

    # 4. Error Tracking
    try:
        # sys.path might need root added if not there yet?
        # app.py adds it. If we run this function from app.py, sys.path should be fine.
        from utils.error_tracking import init_error_tracking
        init_error_tracking(environment=os.getenv("ENVIRONMENT", "development"))
    except ImportError:
        logging.debug("Error tracking module not found, skipping.")

    # 5. Streamlit Page Config
    # Check if already configured (Streamlit warns if set twice, but we want this to be the source of truth)
    try:
        st.set_page_config(
            page_title="Brooks Data Center Daily Briefing",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': None,
                'Report a bug': None,
                'About': "Brooks Data Center Daily Briefing - Desktop Application"
            }
        )
    except Exception as e:
        # set_page_config can only be called once.
        logging.debug(f"set_page_config skipped or failed: {e}")

