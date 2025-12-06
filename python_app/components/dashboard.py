"""
Dashboard overview component for Streamlit app.
Uses Node.js API for data fetching.
"""

import streamlit as st
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging
import pandas as pd

from python_app.utils.api_client import get_health_status
from gcp_clients import get_firestore_client
from python_app.services.market_data_service import fetch_watchlist_intraday_data

logger = logging.getLogger(__name__)


@st.cache_data(ttl=300)  # 5-minute cache
def _get_report_stats(_firestore_client, client_id: str = "michael_brooks") -> Dict:
    """Get statistics from Firestore."""
    try:
        db = _firestore_client
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
def _get_recent_activity(_firestore_client, client_id: str = "michael_brooks", limit: int = 10) -> List[Dict]:
    """Get recent activity timeline."""
    try:
        db = _firestore_client
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
    
    st.divider()
    
    # Market Pulse Section
    st.subheader("Market Pulse (Real-time)")
    
    # Get watchlist from session state or default
    watchlist = st.session_state.get("watchlist", [])
    if not watchlist:
        st.info("No tickers in watchlist to analyze.")
    else:
        # Fetch market data
        try:
            df = fetch_watchlist_intraday_data(watchlist, datetime.now().date())
            
            if not df.empty:
                # Top Movers (by Change %)
                st.markdown("##### 🔥 Top Movers")
                top_movers = df.sort_values("change_pct", ascending=False).head(3)
                
                cols = st.columns(3)
                for i, (_, row) in enumerate(top_movers.iterrows()):
                    with cols[i]:
                        ticker = row['ticker']
                        change = row['change_pct']
                        price = row['last_price']
                        
                        st.metric(
                            label=ticker,
                            value=f"${price:,.2f}" if pd.notnull(price) else "N/A",
                            delta=f"{change:+.2f}%" if pd.notnull(change) else "N/A"
                        )
                
                st.markdown("---")
                
                # Detailed Metrics Table
                st.markdown("##### 📈 Detailed Metrics")
                
                # formatting for display
                display_df = df.copy()
                
                # Calculate Metrics
                # RVOL
                display_df['RVOL'] = display_df.apply(
                    lambda x: x['volume'] / x['average_volume'] if pd.notnull(x['volume']) and pd.notnull(x['average_volume']) and x['average_volume'] > 0 else None, 
                    axis=1
                )
                
                # Gap %
                display_df['Gap %'] = display_df.apply(
                    lambda x: (x['open'] - x['prev_close']) / x['prev_close'] * 100.0 if pd.notnull(x['open']) and pd.notnull(x['prev_close']) else None,
                    axis=1
                )
                
                # Day Range %
                display_df['Range %'] = display_df.apply(
                    lambda x: (x['day_high'] - x['day_low']) / x['prev_close'] * 100.0 if pd.notnull(x['day_high']) and pd.notnull(x['day_low']) and pd.notnull(x['prev_close']) else None,
                    axis=1
                )
                 
                # Intraday Position (0-100%)
                display_df['Position %'] = display_df.apply(
                    lambda x: (x['last_price'] - x['day_low']) / (x['day_high'] - x['day_low']) * 100.0 if pd.notnull(x['last_price']) and pd.notnull(x['day_high']) and pd.notnull(x['day_low']) and (x['day_high'] != x['day_low']) else None,
                    axis=1
                )

                # Format columns
                final_df = display_df[['ticker', 'last_price', 'change_pct', 'RVOL', 'Gap %', 'Range %', 'Position %']].copy()
                
                # Rename for UI
                final_df.columns = ['Ticker', 'Price', 'Change %', 'RVOL', 'Gap %', 'Range %', 'Pos %']
                
                st.dataframe(
                    final_df.style.format({
                        'Price': '${:,.2f}',
                        'Change %': '{:+.2f}%',
                        'RVOL': '{:.2f}x',
                        'Gap %': '{:+.2f}%',
                        'Range %': '{:.2f}%',
                        'Pos %': '{:.0f}%'
                    }).background_gradient(subset=['Change %', 'Gap %'], cmap='RdYlGn', vmin=-3, vmax=3),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("Unable to fetch market data at this time.")
                
        except Exception as e:
            logger.error(f"Error rendering Market Pulse: {e}")
            st.error("Failed to load market metrics.")

    # System health status
    st.divider()
    st.subheader("System Health")
    
    try:
        health = get_health_status()
        if health.get("status") == "healthy":
            st.success("✅ All systems operational")
        else:
            st.warning("⚠️ Some systems may be experiencing issues")
            
        # Show component statuses (hide technical errors from users)
        components = health.get("components", {})
        for component, status_info in components.items():
            status = status_info.get("status", "unknown")
            if status == "healthy":
                st.write(f"✅ {component.title()}")
            else:
                # Don't show technical error details to users
                st.write(f"⚠️ {component.title()}")
    except Exception as e:
        from utils.user_messages import get_user_friendly_message
        st.error(get_user_friendly_message("health_check_failed"))

