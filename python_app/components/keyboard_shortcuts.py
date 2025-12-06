"""
Keyboard shortcuts for desktop navigation.

Streamlit doesn't natively support keyboard shortcuts, but we can use
JavaScript injection to add keyboard navigation support.
"""

import streamlit as st
from typing import Dict, Callable, Optional


# Keyboard shortcut mappings
_SHORTCUTS: Dict[str, Dict[str, any]] = {
    "g": {
        "description": "Generate report",
        "action": "generate_report",
        "key": "g"
    },
    "r": {
        "description": "Refresh data",
        "action": "refresh",
        "key": "r"
    },
    "1": {
        "description": "Switch to Dashboard tab",
        "action": "tab_dashboard",
        "key": "1"
    },
    "2": {
        "description": "Switch to Watchlist Report tab",
        "action": "tab_watchlist",
        "key": "2"
    },
    "3": {
        "description": "Switch to Report History tab",
        "action": "tab_history",
        "key": "3"
    },
    "4": {
        "description": "Switch to AI Chat tab",
        "action": "tab_chat",
        "key": "4"
    },
    "?": {
        "description": "Show keyboard shortcuts",
        "action": "show_shortcuts",
        "key": "?"
    },
    "Escape": {
        "description": "Close dialogs/modals",
        "action": "escape",
        "key": "Escape"
    }
}


def render_keyboard_shortcuts_help() -> None:
    """Render a help dialog showing available keyboard shortcuts."""
    with st.expander("⌨️ Keyboard Shortcuts", expanded=False):
        st.markdown("""
        **Navigation:**
        - `1` - Dashboard tab
        - `2` - Watchlist Report tab
        - `3` - Report History tab
        - `4` - AI Chat tab
        
        **Actions:**
        - `G` - Generate report (when on Dashboard)
        - `R` - Refresh data
        - `?` - Show this help
        
        **General:**
        - `Esc` - Close dialogs/modals
        """)
        
        # Show all shortcuts in a table
        st.markdown("### All Shortcuts")
        shortcut_data = []
        for key, info in _SHORTCUTS.items():
            shortcut_data.append({
                "Key": f"`{key}`",
                "Action": info["description"]
            })
        
        import pandas as pd
        df = pd.DataFrame(shortcut_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def inject_keyboard_shortcuts_js() -> None:
    """
    Inject JavaScript to handle keyboard shortcuts.
    
    Note: Streamlit's architecture makes it difficult to implement true
    keyboard shortcuts that trigger Python callbacks. This function sets up
    the JavaScript infrastructure, but actual shortcut handling would need
    to be implemented via Streamlit's component system or by using
    streamlit-js-eval or similar.
    """
    st.markdown("""
    <script>
    // Keyboard shortcuts handler
    document.addEventListener('keydown', function(e) {
        // Don't trigger shortcuts when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
            return;
        }
        
        const key = e.key;
        const keyCode = e.keyCode || e.which;
        
        // Handle shortcuts
        switch(key) {
            case '1':
                // Navigate to Dashboard
                window.location.hash = '#dashboard';
                break;
            case '2':
                // Navigate to Watchlist Report
                window.location.hash = '#watchlist';
                break;
            case '3':
                // Navigate to Report History
                window.location.hash = '#history';
                break;
            case '4':
                // Navigate to AI Chat
                window.location.hash = '#chat';
                break;
            case 'g':
            case 'G':
                // Generate report - trigger button click if available
                const generateBtn = document.querySelector('button:contains("Generate")');
                if (generateBtn) {
                    generateBtn.click();
                }
                break;
            case 'r':
            case 'R':
                // Refresh - reload page
                if (e.ctrlKey || e.metaKey) {
                    window.location.reload();
                }
                break;
            case '?':
                // Show shortcuts help
                // This would need to be handled via Streamlit state
                break;
            case 'Escape':
                // Close any open modals/dialogs
                const modals = document.querySelectorAll('[role="dialog"]');
                modals.forEach(modal => {
                    if (modal.style.display !== 'none') {
                        modal.style.display = 'none';
                    }
                });
                break;
        }
    });
    </script>
    """, unsafe_allow_html=True)


def get_shortcut_description(key: str) -> Optional[str]:
    """Get the description for a keyboard shortcut."""
    if key in _SHORTCUTS:
        return _SHORTCUTS[key]["description"]
    return None
