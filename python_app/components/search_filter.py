"""
Advanced search and filtering components for reports.

Provides search functionality, filtering, and sorting for report history.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable
from datetime import date, datetime, timedelta
import re


def filter_reports_by_date_range(
    reports: List[Dict[str, Any]],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Filter reports by date range.
    
    Args:
        reports: List of report dictionaries
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        Filtered list of reports
    """
    if not reports:
        return []
    
    filtered = []
    for report in reports:
        trading_date_str = report.get("trading_date", "")
        if not trading_date_str:
            continue
        
        try:
            trading_date = date.fromisoformat(trading_date_str)
            
            if start_date and trading_date < start_date:
                continue
            if end_date and trading_date > end_date:
                continue
            
            filtered.append(report)
        except (ValueError, TypeError):
            continue
    
    return filtered


def filter_reports_by_tickers(
    reports: List[Dict[str, Any]],
    tickers: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter reports that contain any of the specified tickers.
    
    Args:
        reports: List of report dictionaries
        tickers: List of ticker symbols to filter by
        
    Returns:
        Filtered list of reports
    """
    if not reports or not tickers:
        return reports
    
    # Normalize tickers to uppercase
    tickers_upper = [t.upper() for t in tickers]
    
    filtered = []
    for report in reports:
        report_tickers = report.get("tickers", [])
        if not report_tickers:
            continue
        
        # Check if any ticker matches
        report_tickers_upper = [t.upper() if isinstance(t, str) else str(t).upper() for t in report_tickers]
        if any(t in report_tickers_upper for t in tickers_upper):
            filtered.append(report)
    
    return filtered


def search_reports_by_text(
    reports: List[Dict[str, Any]],
    search_query: str,
    search_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Search reports by text content.
    
    Args:
        reports: List of report dictionaries
        search_query: Search query string
        search_fields: List of fields to search in. If None, searches in:
            summary_text, key_insights, market_context
        
    Returns:
        Filtered list of reports matching the search query
    """
    if not reports or not search_query:
        return reports
    
    if search_fields is None:
        search_fields = ["summary_text", "key_insights", "market_context"]
    
    # Case-insensitive search
    search_lower = search_query.lower()
    
    filtered = []
    for report in reports:
        for field in search_fields:
            field_value = report.get(field, "")
            
            if isinstance(field_value, list):
                # For list fields like key_insights
                field_text = " ".join(str(item) for item in field_value).lower()
            else:
                field_text = str(field_value).lower()
            
            if search_lower in field_text:
                filtered.append(report)
                break  # Found a match, no need to check other fields
    
    return filtered


def sort_reports(
    reports: List[Dict[str, Any]],
    sort_by: str = "trading_date",
    ascending: bool = False
) -> List[Dict[str, Any]]:
    """
    Sort reports by a specified field.
    
    Args:
        reports: List of report dictionaries
        sort_by: Field to sort by (trading_date, client_id, etc.)
        ascending: Sort order (True for ascending, False for descending)
        
    Returns:
        Sorted list of reports
    """
    if not reports:
        return []
    
    def get_sort_key(report: Dict[str, Any]) -> Any:
        value = report.get(sort_by)
        
        # Handle date strings
        if sort_by == "trading_date" and isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except (ValueError, TypeError):
                return date.min
        
        # Handle numeric values
        if isinstance(value, (int, float)):
            return value
        
        # Handle strings
        if isinstance(value, str):
            return value.lower()
        
        # Handle lists (use length)
        if isinstance(value, list):
            return len(value)
        
        return value
    
    try:
        sorted_reports = sorted(reports, key=get_sort_key, reverse=not ascending)
        return sorted_reports
    except Exception:
        # If sorting fails, return original order
        return reports


def render_search_filter_ui(
    reports: List[Dict[str, Any]],
    on_filter_change: Optional[Callable[[List[Dict[str, Any]]], None]] = None
) -> List[Dict[str, Any]]:
    """
    Render search and filter UI components.
    
    Args:
        reports: List of all reports
        on_filter_change: Optional callback when filters change
        
    Returns:
        Filtered and sorted list of reports
    """
    st.subheader("🔍 Search & Filter Reports")
    
    # Search bar
    search_query = st.text_input(
        "Search reports",
        placeholder="Search in summary, insights, or context...",
        key="report_search_query"
    )
    
    # Filter options in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Date range filter
        date_filter_enabled = st.checkbox("Filter by date range", key="date_filter_enabled")
        if date_filter_enabled:
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                start_date = st.date_input(
                    "Start date",
                    value=date.today() - timedelta(days=30),
                    key="filter_start_date"
                )
            with date_col2:
                end_date = st.date_input(
                    "End date",
                    value=date.today(),
                    key="filter_end_date"
                )
        else:
            start_date = None
            end_date = None
    
    with col2:
        # Ticker filter
        ticker_filter_enabled = st.checkbox("Filter by tickers", key="ticker_filter_enabled")
        if ticker_filter_enabled:
            ticker_input = st.text_input(
                "Tickers (comma-separated)",
                placeholder="SMCI, NVDA, IREN",
                key="filter_tickers"
            )
            if ticker_input:
                tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
            else:
                tickers = []
        else:
            tickers = []
    
    with col3:
        # Sort options
        sort_by = st.selectbox(
            "Sort by",
            options=["trading_date", "client_id"],
            index=0,
            key="sort_by_field"
        )
        sort_order = st.selectbox(
            "Order",
            options=["Newest first", "Oldest first"],
            index=0,
            key="sort_order"
        )
        ascending = sort_order == "Oldest first"
    
    # Apply filters
    filtered_reports = reports.copy()
    
    # Text search
    if search_query:
        filtered_reports = search_reports_by_text(filtered_reports, search_query)
    
    # Date range filter
    if date_filter_enabled and (start_date or end_date):
        filtered_reports = filter_reports_by_date_range(filtered_reports, start_date, end_date)
    
    # Ticker filter
    if ticker_filter_enabled and tickers:
        filtered_reports = filter_reports_by_tickers(filtered_reports, tickers)
    
    # Sort
    filtered_reports = sort_reports(filtered_reports, sort_by=sort_by, ascending=ascending)
    
    # Show results count
    st.caption(f"Showing {len(filtered_reports)} of {len(reports)} reports")
    
    # Callback if provided
    if on_filter_change:
        on_filter_change(filtered_reports)
    
    return filtered_reports


def highlight_search_terms(text: str, search_query: str) -> str:
    """
    Highlight search terms in text (for display purposes).
    
    Args:
        text: Text to highlight in
        search_query: Search query
        
    Returns:
        Text with HTML highlighting (for use with st.markdown with unsafe_allow_html=True)
    """
    if not search_query or not text:
        return text
    
    # Escape HTML in text
    import html
    text_escaped = html.escape(text)
    
    # Highlight search terms (case-insensitive)
    pattern = re.escape(search_query)
    highlighted = re.sub(
        f"({pattern})",
        r'<mark style="background-color: #10b981; color: #0f172a; padding: 2px 4px; border-radius: 3px;">\1</mark>',
        text_escaped,
        flags=re.IGNORECASE
    )
    
    return highlighted

