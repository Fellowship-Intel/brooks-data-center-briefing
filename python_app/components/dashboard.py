"""
Dashboard overview component for Streamlit app.
Uses Node.js API for data fetching.
"""

import streamlit as st
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

from python_app.utils.api_client import get_health_status
from gcp_clients import get_firestore_client

logger = logging.getLogger(__name__)


@st.cache_data(ttl=300)  # 5-minute cache
def _get_report_stats(firestore_client, client_id: str = "michael_brooks") -> Dict:
    """Get statistics from Firestore."""
    try:
        db = firestore_client
        reports_ref = db.collection("daily_reports")
        
        # Filter by client if needed
        if client_id:
            reports_ref = reports_ref.where("client_id", "==", client_id)
        
        reports = list(reports_ref.stream())
        
        total_reports = len(reports)
        
        # Count reports with audio
        reports_with_audio = sum(1 for r in reports if r.to_dict().get("audio_gcs_path"))
        tts_success_rate = (reports_with_audio / total_reports * 100) if total_reports > 0 else 0
        
        # Get last report date
        if reports:
            last_report = max(reports, key=lambda r: r.to_dict().get("trading_date", ""))
            last_date = last_report.to_dict().get("trading_date")
        else:
            last_date = None
        
        # Average generation time (placeholder - would need metrics)
        avg_generation_time = "N/A"
        
        return {
            "total_reports": total_reports,
            "tts_success_rate": round(tts_success_rate, 1),
            "avg_generation_time": avg_generation_time,
            "last_report_date": last_date,
        }
    except Exception as e:
        logger.error(f"Error fetching report stats: {e}")
        return {
            "total_reports": 0,
            "tts_success_rate": 0,
            "avg_generation_time": "N/A",
            "last_report_date": None,
        }


@st.cache_data(ttl=300)
def _get_recent_activity(firestore_client, client_id: str = "michael_brooks", limit: int = 10) -> List[Dict]:
    """Get recent activity timeline."""
    try:
        db = firestore_client
        reports_ref = db.collection("daily_reports")
        
        if client_id:
            reports_ref = reports_ref.where("client_id", "==", client_id)
        
        reports_ref = reports_ref.order_by("trading_date", direction="DESCENDING").limit(limit)
        reports = list(reports_ref.stream())
        
        activity = []
        for report in reports:
            data = report.to_dict()
            audio_path = data.get("audio_gcs_path")
            tts_provider = data.get("tts_provider", "N/A")
            
            if audio_path:
                status = "success"
            elif data.get("summary_text"):
                status = "partial"
            else:
                status = "failed"
            
            activity.append({
                "date": data.get("trading_date"),
                "client": data.get("client_id", "Unknown"),
                "tts_provider": tts_provider,
                "status": status,
                "id": report.id,
            })
        
        return activity
    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}")
        return []


def render_dashboard(firestore_client, client_id: str = "michael_brooks"):
    """
    Render dashboard overview component.
    
    Args:
        firestore_client: Firestore client instance
        client_id: Client ID to filter reports
    """
    st.title("📊 Dashboard Overview")
    
    # Get statistics
    stats = _get_report_stats(firestore_client, client_id)
    
    # Key metrics in 4 columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Reports",
            stats["total_reports"],
            delta=None,
        )
    
    with col2:
        st.metric(
            "TTS Success Rate",
            f"{stats['tts_success_rate']}%",
            delta=None,
        )
    
    with col3:
        st.metric(
            "Avg Generation Time",
            stats["avg_generation_time"],
            delta=None,
        )
    
    with col4:
        last_date = stats["last_report_date"]
        if last_date:
            st.metric(
                "Last Report Date",
                last_date,
                delta=None,
            )
        else:
            st.metric("Last Report Date", "None", delta=None)
    
    st.divider()
    
    # Recent activity timeline
    st.subheader("Recent Activity")
    activity = _get_recent_activity(firestore_client, client_id, limit=10)
    
    if activity:
        for item in activity:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
                
                with col1:
                    st.write(f"**{item['date']}**")
                
                with col2:
                    st.write(item['client'])
                
                with col3:
                    st.write(f"TTS: {item['tts_provider']}")
                
                with col4:
                    status_emoji = {
                        "success": "✅",
                        "partial": "⚠️",
                        "failed": "❌",
                    }
                    st.write(status_emoji.get(item['status'], "❓"))
                
                with col5:
                    if st.button("View", key=f"view_{item['id']}"):
                        st.session_state['selected_report_date'] = item['date']
                        st.rerun()
                
                st.divider()
    else:
        st.info("No recent activity to display.")
    
    # System health status
    st.divider()
    st.subheader("System Health")
    
    try:
        health = get_health_status()
        if health.get("status") == "healthy":
            st.success("✅ All systems operational")
        else:
            st.warning("⚠️ Some systems may be experiencing issues")
            
        # Show component statuses
        components = health.get("components", {})
        for component, status_info in components.items():
            status = status_info.get("status", "unknown")
            if status == "healthy":
                st.write(f"✅ {component.title()}")
            else:
                st.write(f"❌ {component.title()}: {status_info.get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Could not fetch health status: {e}")

