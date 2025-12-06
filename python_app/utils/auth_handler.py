"""
Authentication Handler for Streamlit App.
Handles Google OAuth flow, session management, and login UI.
"""
import streamlit as st
import os
import logging
from typing import Optional, Dict
from utils.oauth import get_login_url, get_google_flow, verify_google_token

logger = logging.getLogger(__name__)

def render_login_page(auth_url: str):
    """Renders the login page."""
    st.title("Sign In")
    st.markdown("Please sign in with your Google account to access the Brooks Data Center Daily Briefing.")
    
    st.markdown(
        f"""
        <a href="{auth_url}" target="_self">
            <button style="
                background-color: #4285F4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <svg width="18" height="18" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                    <path fill="none" d="M0 0h48v48H0z"/>
                </svg>
                Sign in with Google
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )
    
    if os.environ.get("ENVIRONMENT") == "development":
        st.divider()
        if st.button("Initialize Dev Auth (Analysis Mode)"):
            st.session_state.user_info = {
                "email": "dev@example.com",
                "name": "Developer",
                "sub": "dev-user-123"
            }
            st.rerun()

def handle_auth():
    """
    Main authentication handler.
    Must be called at the start of the app.
    """
    if "user_info" in st.session_state:
        return

    # Check for auth code in query params
    query_params = st.query_params
    code = query_params.get("code")

    try:
        # Determine redirect URI 
        # In Streamlit Cloud this is tricky, locally it's localhost
        # We assume the app is running at the root
        # Using a fixed URI for now, might need configuration
        redirect_uri = os.environ.get("REDIRECT_URI", "http://localhost:8080")
        
        if code:
            # Exchange code for token
            flow = get_google_flow(redirect_uri)
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Verify ID token
            user_info = verify_google_token(credentials.id_token)
            
            if user_info:
                st.session_state.user_info = user_info
                # Clear query params
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Auhentication failed: Invalid token")
        
        # Show login page
        auth_url = get_login_url(redirect_uri)
        render_login_page(auth_url)
        st.stop()
        
    except Exception as e:
        if os.environ.get("ENVIRONMENT") == "development":
             # If secrets missing, fallback to dev mode
             st.warning(f"Auth configuration error: {e}")
             render_login_page("#")
             st.stop()
        else:
             logger.error(f"Auth error: {e}")
             st.error("Authentication system error. Please contact support.")
             st.stop()

def get_current_user() -> Optional[Dict[str, str]]:
    """Returns the current authenticated user."""
    return st.session_state.get("user_info")
