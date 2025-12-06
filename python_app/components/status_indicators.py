"""
Status indicators component for system health monitoring.
Uses Node.js API for health checks.
"""

import streamlit as st
from typing import Dict, Any
import logging
import time

from python_app.utils.api_client import get_health_status

logger = logging.getLogger(__name__)


@st.cache_data(ttl=60)  # 60-second cache
def _check_service_status() -> Dict[str, Dict[str, Any]]:
    """Check status of all services."""
    try:
        health = get_health_status()
        components = health.get("components", {})
        
        statuses = {}
        for component, status_info in components.items():
            status = status_info.get("status", "unknown")
            error = status_info.get("error")
            
            if status == "healthy":
                statuses[component] = {
                    "status": "healthy",
                    "emoji": "🟢",
                    "color": "#10b981",
                }
            elif status == "unhealthy":
                statuses[component] = {
                    "status": "degraded",
                    "emoji": "🔴",
                    "color": "#ef4444",
                    "error": error,
                }
            else:
                statuses[component] = {
                    "status": "unknown",
                    "emoji": "🟡",
                    "color": "#f59e0b",
                }
        
        return statuses
    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        return {
            "api": {
                "status": "unknown",
                "emoji": "🟡",
                "color": "#f59e0b",
                "error": str(e),
            }
        }


def render_status_indicators(show_in_sidebar: bool = True) -> None:
    """
    Render system health status indicators.
    
    Args:
        show_in_sidebar: If True, render in sidebar; otherwise render in main area
    """
    container = st.sidebar if show_in_sidebar else st
    
    with container.expander("🔍 System Health", expanded=False):
        statuses = _check_service_status()
        
        if not statuses:
            st.info("No service status available")
            return
        
        # Display each service status
        for component, status_info in statuses.items():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown(f"<span style='font-size: 1.2em;'>{status_info['emoji']}</span>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**{component.replace('_', ' ').title()}**")
                if status_info.get("error"):
                    st.caption(f"Error: {status_info['error'][:50]}...")
        
        # Refresh button
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Last update timestamp
        st.caption(f"Last updated: {time.strftime('%H:%M:%S')}")

