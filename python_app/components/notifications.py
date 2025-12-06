"""
Desktop notifications for report completion and important events.

Provides desktop notification support for desktop applications.
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def show_browser_notification(
    title: str,
    message: str,
    icon: str = "📊",
    duration: int = 5000
) -> None:
    """
    Show a browser-based notification using JavaScript.
    
    Note: Browser notifications require user permission and may not work
    in all browsers or when the page is not in focus.
    
    Args:
        title: Notification title
        message: Notification message
        icon: Emoji icon to display
        duration: Duration in milliseconds (default: 5000)
    """
    notification_js = f"""
    <script>
    if ("Notification" in window) {{
        if (Notification.permission === "granted") {{
            new Notification("{title}", {{
                body: "{icon} {message}",
                icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'><text y='.9em' font-size='90'>{icon}</text></svg>",
                tag: "report-notification",
                requireInteraction: false
            }});
        }} else if (Notification.permission !== "denied") {{
            Notification.requestPermission().then(function (permission) {{
                if (permission === "granted") {{
                    new Notification("{title}", {{
                        body: "{icon} {message}",
                        icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'><text y='.9em' font-size='90'>{icon}</text></svg>",
                        tag: "report-notification"
                    }});
                }}
            }});
        }}
    }}
    </script>
    """
    st.markdown(notification_js, unsafe_allow_html=True)


def request_notification_permission() -> None:
    """
    Request browser notification permission from the user.
    """
    permission_js = """
    <script>
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }
    </script>
    """
    st.markdown(permission_js, unsafe_allow_html=True)


def notify_report_complete(
    trading_date: str,
    client_id: str,
    has_audio: bool = False
) -> None:
    """
    Show notification when report generation is complete.
    
    Args:
        trading_date: Trading date of the report
        client_id: Client ID
        has_audio: Whether audio was generated
    """
    message = f"Daily report for {trading_date} is ready!"
    if has_audio:
        message += " Audio available."
    
    show_browser_notification(
        title="Report Complete",
        message=message,
        icon="✅"
    )


def notify_report_error(
    error_message: str,
    trading_date: Optional[str] = None
) -> None:
    """
    Show notification when report generation fails.
    
    Args:
        error_message: Error message
        trading_date: Optional trading date
    """
    message = error_message
    if trading_date:
        message = f"Report generation failed for {trading_date}: {error_message}"
    
    show_browser_notification(
        title="Report Generation Error",
        message=message,
        icon="❌"
    )


def notify_rate_limit(
    retry_after: Optional[int] = None
) -> None:
    """
    Show notification when rate limit is exceeded.
    
    Args:
        retry_after: Optional seconds to wait before retry
    """
    message = "Rate limit exceeded. Please wait before generating another report."
    if retry_after:
        message += f" Retry after {retry_after} seconds."
    
    show_browser_notification(
        title="Rate Limit Exceeded",
        message=message,
        icon="⏱️"
    )


def render_notification_settings() -> None:
    """
    Render notification settings UI in the sidebar or settings section.
    """
    with st.expander("🔔 Notification Settings", expanded=False):
        st.markdown("Enable desktop notifications for:")
        
        notify_on_complete = st.checkbox(
            "Report completion",
            value=True,
            key="notify_on_complete"
        )
        
        notify_on_error = st.checkbox(
            "Report errors",
            value=True,
            key="notify_on_error"
        )
        
        notify_on_rate_limit = st.checkbox(
            "Rate limit warnings",
            value=True,
            key="notify_on_rate_limit"
        )
        
        # Request permission button
        if st.button("Request Notification Permission"):
            request_notification_permission()
            st.info("Check your browser for a permission prompt.")
        
        # Show current permission status
        permission_js = """
        <script>
        if ("Notification" in window) {
            const status = Notification.permission;
            const statusElement = document.createElement('div');
            statusElement.innerHTML = `Permission: <strong>${status}</strong>`;
            statusElement.style.marginTop = '10px';
            statusElement.style.padding = '10px';
            statusElement.style.backgroundColor = status === 'granted' ? '#10b98120' : '#ef444420';
            statusElement.style.borderRadius = '5px';
            document.currentScript.parentElement.appendChild(statusElement);
        }
        </script>
        """
        st.markdown(permission_js, unsafe_allow_html=True)

