"""
Enhanced report viewer component with comparison and bookmarking features.

Provides advanced viewing capabilities including side-by-side comparison,
bookmarking, and annotations.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import date
from report_repository import get_daily_report, get_firestore_client
from firebase_admin import firestore


def save_bookmark(trading_date: str, client_id: str, notes: Optional[str] = None) -> None:
    """
    Save a report as a bookmark.
    
    Args:
        trading_date: Trading date of the report to bookmark
        client_id: Client ID
        notes: Optional notes for the bookmark
    """
    try:
        db = get_firestore_client()
        bookmarks_ref = db.collection("bookmarks")
        
        bookmark_id = f"{client_id}_{trading_date}"
        bookmark_data = {
            "client_id": client_id,
            "trading_date": trading_date,
            "notes": notes or "",
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        
        bookmarks_ref.document(bookmark_id).set(bookmark_data, merge=True)
        st.success("✅ Report bookmarked!")
    except Exception as e:
        st.error(f"Failed to save bookmark: {str(e)}")


def remove_bookmark(trading_date: str, client_id: str) -> None:
    """
    Remove a bookmark.
    
    Args:
        trading_date: Trading date of the report to unbookmark
        client_id: Client ID
    """
    try:
        db = get_firestore_client()
        bookmark_id = f"{client_id}_{trading_date}"
        db.collection("bookmarks").document(bookmark_id).delete()
        st.success("Bookmark removed")
    except Exception as e:
        st.error(f"Failed to remove bookmark: {str(e)}")


def get_bookmarks(client_id: str) -> List[Dict[str, Any]]:
    """
    Get all bookmarks for a client.
    
    Args:
        client_id: Client ID
        
    Returns:
        List of bookmark dictionaries
    """
    try:
        db = get_firestore_client()
        bookmarks = db.collection("bookmarks").where("client_id", "==", client_id).stream()
        
        result = []
        for doc in bookmarks:
            data = doc.to_dict()
            data["id"] = doc.id
            result.append(data)
        
        # Sort by trading_date descending
        result.sort(key=lambda x: x.get("trading_date", ""), reverse=True)
        return result
    except Exception as e:
        st.error(f"Failed to load bookmarks: {str(e)}")
        return []


def is_bookmarked(trading_date: str, client_id: str) -> bool:
    """
    Check if a report is bookmarked.
    
    Args:
        trading_date: Trading date
        client_id: Client ID
        
    Returns:
        True if bookmarked, False otherwise
    """
    try:
        db = get_firestore_client()
        bookmark_id = f"{client_id}_{trading_date}"
        doc = db.collection("bookmarks").document(bookmark_id).get()
        return doc.exists
    except Exception:
        return False


def render_report_comparison(
    report1_date: str,
    report2_date: str,
    client_id: str
) -> None:
    """
    Render side-by-side comparison of two reports.
    
    Args:
        report1_date: Trading date of first report
        report2_date: Trading date of second report
        client_id: Client ID
    """
    st.header("📊 Report Comparison")
    
    report1 = get_daily_report(report1_date)
    report2 = get_daily_report(report2_date)
    
    if not report1:
        st.error(f"Report for {report1_date} not found")
        return
    if not report2:
        st.error(f"Report for {report2_date} not found")
        return
    
    # Comparison metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Report 1 Date", report1_date)
        st.metric("Tickers", len(report1.get("tickers", [])))
    with col2:
        st.metric("Report 2 Date", report2_date)
        st.metric("Tickers", len(report2.get("tickers", [])))
    with col3:
        # Common tickers
        tickers1 = set(report1.get("tickers", []))
        tickers2 = set(report2.get("tickers", []))
        common = tickers1 & tickers2
        st.metric("Common Tickers", len(common))
    
    st.divider()
    
    # Side-by-side comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📅 {report1_date}")
        st.markdown("**Summary:**")
        summary1 = report1.get("summary_text", "")
        if summary1:
            st.write(summary1[:500] + "..." if len(summary1) > 500 else summary1)
        
        insights1 = report1.get("key_insights", [])
        if insights1:
            st.markdown("**Key Insights:**")
            for insight in insights1[:3]:  # Show first 3
                st.markdown(f"- {insight}")
    
    with col2:
        st.subheader(f"📅 {report2_date}")
        st.markdown("**Summary:**")
        summary2 = report2.get("summary_text", "")
        if summary2:
            st.write(summary2[:500] + "..." if len(summary2) > 500 else summary2)
        
        insights2 = report2.get("key_insights", [])
        if insights2:
            st.markdown("**Key Insights:**")
            for insight in insights2[:3]:  # Show first 3
                st.markdown(f"- {insight}")
    
    # Ticker comparison
    st.divider()
    st.subheader("Ticker Comparison")
    
    if common:
        st.info(f"Common tickers: {', '.join(sorted(common))}")
    
    # Unique to each report
    unique1 = tickers1 - tickers2
    unique2 = tickers2 - tickers1
    
    comp_col1, comp_col2 = st.columns(2)
    with comp_col1:
        if unique1:
            st.markdown(f"**Only in {report1_date}:**")
            st.write(", ".join(sorted(unique1)))
    with comp_col2:
        if unique2:
            st.markdown(f"**Only in {report2_date}:**")
            st.write(", ".join(sorted(unique2)))


def render_bookmark_management(client_id: str) -> None:
    """
    Render bookmark management UI.
    
    Args:
        client_id: Client ID
    """
    st.subheader("🔖 Bookmarked Reports")
    
    bookmarks = get_bookmarks(client_id)
    
    if not bookmarks:
        st.info("No bookmarked reports. Bookmark reports from the Report History tab.")
        return
    
    for bookmark in bookmarks:
        trading_date = bookmark.get("trading_date", "Unknown")
        notes = bookmark.get("notes", "")
        
        with st.expander(f"📌 {trading_date}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if notes:
                    st.write(f"**Notes:** {notes}")
                
                if st.button("📄 View Report", key=f"view_bookmark_{trading_date}"):
                    st.session_state['selected_report_date'] = trading_date
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Remove", key=f"remove_bookmark_{trading_date}"):
                    remove_bookmark(trading_date, client_id)
                    st.rerun()


def render_bookmark_button(trading_date: str, client_id: str) -> None:
    """
    Render a bookmark/unbookmark button for a report.
    
    Args:
        trading_date: Trading date
        client_id: Client ID
    """
    is_booked = is_bookmarked(trading_date, client_id)
    
    if is_booked:
        if st.button("🔖 Bookmarked", key=f"bookmark_{trading_date}", help="Click to remove bookmark"):
            remove_bookmark(trading_date, client_id)
            st.rerun()
    else:
        if st.button("🔖 Bookmark", key=f"bookmark_{trading_date}", help="Save this report for quick access"):
            # Show notes input
            with st.popover("Add Bookmark Notes"):
                notes = st.text_area("Notes (optional)", key=f"bookmark_notes_{trading_date}")
                if st.button("Save Bookmark", key=f"save_bookmark_{trading_date}"):
                    save_bookmark(trading_date, client_id, notes)
                    st.rerun()

