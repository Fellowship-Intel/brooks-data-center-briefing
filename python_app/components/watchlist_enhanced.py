"""
Enhanced watchlist management with categorization and bulk operations.

Provides advanced watchlist features including categories, tags, and bulk import/export.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from report_repository import get_client, create_or_update_client
from utils.bulk_operations import import_watchlist_from_csv, export_watchlist_to_csv
from utils.input_validation import validate_ticker_list


def get_watchlist_categories(client_id: str) -> Dict[str, List[str]]:
    """
    Get watchlist organized by categories.
    
    Args:
        client_id: Client ID
        
    Returns:
        Dictionary mapping category names to lists of tickers
    """
    try:
        client = get_client(client_id)
        if client and "watchlist_categories" in client:
            return client.get("watchlist_categories", {})
    except Exception:
        pass
    
    return {}


def save_watchlist_categories(client_id: str, categories: Dict[str, List[str]]) -> bool:
    """
    Save watchlist categories to Firestore.
    
    Args:
        client_id: Client ID
        categories: Dictionary mapping category names to lists of tickers
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client(client_id)
        if client:
            client["watchlist_categories"] = categories
            create_or_update_client(client_id, **client)
        else:
            create_or_update_client(
                client_id,
                watchlist_categories=categories
            )
        return True
    except Exception as e:
        st.error(f"Failed to save categories: {str(e)}")
        return False


def render_watchlist_categories(
    watchlist: List[str],
    client_id: str,
    on_update: Optional[callable] = None
) -> None:
    """
    Render watchlist with category management.
    
    Args:
        watchlist: Current watchlist
        client_id: Client ID
        on_update: Optional callback when watchlist is updated
    """
    st.subheader("📂 Watchlist Categories")
    
    categories = get_watchlist_categories(client_id)
    
    # Default category for uncategorized
    if "Uncategorized" not in categories:
        categories["Uncategorized"] = []
    
    # Ensure all watchlist items are in a category
    all_categorized = []
    for cat_tickers in categories.values():
        all_categorized.extend(cat_tickers)
    
    uncategorized = [t for t in watchlist if t not in all_categorized]
    if uncategorized:
        categories["Uncategorized"].extend(uncategorized)
        categories["Uncategorized"] = list(set(categories["Uncategorized"]))
    
    # Display categories
    for category_name, tickers in categories.items():
        if not tickers:
            continue
        
        with st.expander(f"📁 {category_name} ({len(tickers)})", expanded=False):
            for ticker in tickers:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(ticker)
                with col2:
                    # Move to different category
                    new_category = st.selectbox(
                        "Move to",
                        options=list(categories.keys()) + ["New Category"],
                        key=f"move_{ticker}_{category_name}",
                        index=0
                    )
                    if new_category and new_category != category_name:
                        if new_category == "New Category":
                            new_cat_name = st.text_input("Category name", key=f"new_cat_{ticker}")
                            if new_cat_name:
                                if new_cat_name not in categories:
                                    categories[new_cat_name] = []
                                categories[category_name].remove(ticker)
                                categories[new_cat_name].append(ticker)
                                save_watchlist_categories(client_id, categories)
                                if on_update:
                                    on_update()
                                st.rerun()
                        else:
                            categories[category_name].remove(ticker)
                            categories[new_category].append(ticker)
                            save_watchlist_categories(client_id, categories)
                            if on_update:
                                on_update()
                            st.rerun()
                with col3:
                    if st.button("Remove", key=f"remove_{ticker}_{category_name}"):
                        categories[category_name].remove(ticker)
                        save_watchlist_categories(client_id, categories)
                        if on_update:
                            on_update()
                        st.rerun()
    
    # Add new category
    st.divider()
    with st.expander("➕ Add New Category"):
        new_category_name = st.text_input("Category Name", key="new_category_name")
        category_tickers = st.multiselect(
            "Select Tickers",
            options=watchlist,
            key="category_tickers"
        )
        if st.button("Create Category", key="create_category"):
            if new_category_name and category_tickers:
                if new_category_name not in categories:
                    categories[new_category_name] = []
                categories[new_category_name].extend(category_tickers)
                # Remove from other categories
                for cat_name, cat_tickers in categories.items():
                    if cat_name != new_category_name:
                        categories[cat_name] = [t for t in cat_tickers if t not in category_tickers]
                save_watchlist_categories(client_id, categories)
                if on_update:
                    on_update()
                st.success(f"Category '{new_category_name}' created!")
                st.rerun()


def render_watchlist_bulk_operations(
    watchlist: List[str],
    client_id: str,
    on_update: Optional[callable] = None
) -> None:
    """
    Render bulk operations for watchlist (import/export).
    
    Args:
        watchlist: Current watchlist
        client_id: Client ID
        on_update: Optional callback when watchlist is updated
    """
    st.subheader("📥 Bulk Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Export Watchlist**")
        try:
            csv_bytes = export_watchlist_to_csv(watchlist)
            st.download_button(
                label="📊 Export to CSV",
                data=csv_bytes,
                file_name="watchlist.csv",
                mime="text/csv",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
    
    with col2:
        st.markdown("**Import Watchlist**")
        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=["csv"],
            key="watchlist_import_file"
        )
        if uploaded_file:
            try:
                csv_content = uploaded_file.read()
                imported_tickers = import_watchlist_from_csv(csv_content)
                
                if imported_tickers:
                    st.success(f"Imported {len(imported_tickers)} tickers")
                    st.write(f"Tickers: {', '.join(imported_tickers)}")
                    
                    if st.button("Add to Watchlist", key="add_imported_tickers"):
                        # Validate and merge
                        validated = validate_ticker_list(imported_tickers)
                        # Merge with existing (avoid duplicates)
                        updated_watchlist = list(set(watchlist + validated))
                        
                        if on_update:
                            on_update(updated_watchlist)
                        else:
                            st.session_state.watchlist = updated_watchlist
                        
                        st.success(f"Added {len(validated)} tickers to watchlist")
                        st.rerun()
            except Exception as e:
                st.error(f"Import failed: {str(e)}")

