"""
Help center and onboarding component.

Provides interactive tutorial, FAQ, and documentation links.
"""

import streamlit as st
from typing import Dict, List


FAQ_ITEMS = [
    {
        "question": "How do I generate a daily report?",
        "answer": """
        You can generate a daily report in two ways:
        1. **Dashboard Tab**: Click the "🚀 Generate Daily Market Report" button
        2. **Daily Watchlist Report Tab**: Select a trading date and click "Generate today's watchlist report"
        
        Reports are automatically generated using your watchlist and stored in Firestore.
        """
    },
    {
        "question": "How do I add tickers to my watchlist?",
        "answer": """
        In the sidebar, you'll find the Watchlist section. You can:
        - Type a ticker symbol in the "Add ticker" field and click "Add"
        - Use the "Advanced" tab to import from CSV
        - Organize tickers into categories
        
        The watchlist is automatically saved to Firestore.
        """
    },
    {
        "question": "What is the difference between the report tabs?",
        "answer": """
        - **Top Movers**: Quick overview of the biggest price movers with mini reports
        - **Deep Dive (Core)**: Detailed analysis of core tickers in your watchlist
        - **Full Narrative**: Complete report with all sections and audio script
        """
    },
    {
        "question": "How do I compare two reports?",
        "answer": """
        Go to the "Report History" tab, then click on the "Compare Reports" sub-tab.
        Select two different trading dates and click "Compare Reports" to see a side-by-side comparison.
        """
    },
    {
        "question": "Can I bookmark reports?",
        "answer": """
        Yes! In the Report History tab, you'll see a bookmark button (🔖) next to each report.
        Click it to save the report for quick access. View all bookmarks in the "Bookmarks" sub-tab.
        """
    },
    {
        "question": "How do I export reports?",
        "answer": """
        Reports can be exported in multiple formats:
        - **PDF**: Full report as PDF document
        - **CSV**: Report data and market data as CSV files
        - **Bulk Export**: Export multiple reports at once (ZIP, JSON, CSV)
        
        Export buttons are available in the report view and history sections.
        """
    },
    {
        "question": "What keyboard shortcuts are available?",
        "answer": """
        - `1-4`: Navigate between tabs (Dashboard, Watchlist Report, Report History, AI Chat)
        - `G`: Generate report (when on Dashboard)
        - `R`: Refresh data
        - `?`: Show keyboard shortcuts help
        - `Esc`: Close dialogs/modals
        
        View all shortcuts in the sidebar under "⌨️ Keyboard Shortcuts".
        """
    },
    {
        "question": "How do I customize report settings?",
        "answer": """
        Click on "⚙️ Report Settings" in the sidebar to:
        - Toggle which sections to display
        - Adjust detail level (minimal, standard, detailed)
        - Select report templates
        - Save your preferences
        
        Settings are saved per client and persist across sessions.
        """
    },
    {
        "question": "What if report generation fails?",
        "answer": """
        The app includes automatic error handling:
        - TTS failures don't break the pipeline (text reports still generated)
        - Automatic retry mechanisms for API calls
        - Fallback providers (Eleven Labs → Gemini TTS)
        - Detailed error messages in the UI
        
        Check the sidebar "🔍 System Health" for service status.
        """
    },
    {
        "question": "How do I search for specific reports?",
        "answer": """
        In the Report History tab, use the search bar to:
        - Search by text in summaries, insights, or context
        - Filter by date range
        - Filter by ticker symbols
        - Sort by date or client
        
        Search results update in real-time as you type.
        """
    },
]


def render_faq() -> None:
    """Render FAQ section."""
    st.subheader("❓ Frequently Asked Questions")
    
    for idx, item in enumerate(FAQ_ITEMS):
        with st.expander(f"**Q: {item['question']}**", expanded=False):
            st.markdown(item['answer'])


def render_quick_start_guide() -> None:
    """Render quick start guide."""
    st.subheader("🚀 Quick Start Guide")
    
    st.markdown("""
    ### Step 1: Set Up Your Watchlist
    1. Go to the sidebar and find the "Watchlist" section
    2. Add your ticker symbols (e.g., SMCI, NVDA, IREN)
    3. Click "💾 Save Watchlist" to persist to Firestore
    
    ### Step 2: Generate Your First Report
    1. Navigate to the "Dashboard" tab
    2. Click "🚀 Generate Daily Market Report"
    3. Wait for the progress tracker to complete
    4. View your report in the "Daily Watchlist Report" tab
    
    ### Step 3: Explore Reports
    - **View History**: Check the "Report History" tab to see past reports
    - **Bookmark Important Reports**: Click the 🔖 button to save reports
    - **Compare Reports**: Use the "Compare Reports" tab to see differences
    
    ### Step 4: Customize Settings
    - Adjust report sections in "⚙️ Report Settings"
    - Enable/disable notifications in "🔔 Notification Settings"
    - Configure keyboard shortcuts
    
    ### Step 5: Export Data
    - Export individual reports as PDF or CSV
    - Use bulk export for multiple reports
    - Export watchlist to CSV for backup
    """)


def render_key_features() -> None:
    """Render key features overview."""
    st.subheader("✨ Key Features")
    
    features = [
        {
            "title": "📊 AI-Powered Reports",
            "description": "Generate comprehensive daily briefings using Google Gemini AI"
        },
        {
            "title": "🎧 Audio Reports",
            "description": "Text-to-speech audio generation with Eleven Labs (primary) and Gemini (fallback)"
        },
        {
            "title": "📈 Advanced Charts",
            "description": "Interactive Plotly charts for performance, volume, and sentiment analysis"
        },
        {
            "title": "🔍 Search & Filter",
            "description": "Powerful search and filtering for report history"
        },
        {
            "title": "🔖 Bookmarks",
            "description": "Save important reports for quick access"
        },
        {
            "title": "📊 Comparison",
            "description": "Side-by-side comparison of reports from different dates"
        },
        {
            "title": "📥 Bulk Operations",
            "description": "Import/export watchlists and bulk export reports"
        },
        {
            "title": "⚙️ Customization",
            "description": "Customize report sections, detail levels, and templates"
        },
    ]
    
    cols = st.columns(2)
    for idx, feature in enumerate(features):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"**{feature['title']}**")
                st.caption(feature['description'])
                st.divider()


def render_documentation_links() -> None:
    """Render documentation and external links."""
    st.subheader("📚 Documentation & Resources")
    
    st.markdown("""
    ### Internal Documentation
    - **Component Documentation**: See `python_app/components/README.md`
    - **API Documentation**: Visit `/docs` when running the FastAPI server
    - **App Status**: See `APP_STATUS.md` for detailed architecture information
    
    ### External Resources
    - **Google Gemini AI**: [Documentation](https://ai.google.dev/docs)
    - **Streamlit**: [Documentation](https://docs.streamlit.io)
    - **Firestore**: [Documentation](https://cloud.google.com/firestore/docs)
    - **Plotly**: [Documentation](https://plotly.com/python/)
    
    ### Support
    - Check system health in the sidebar
    - Review error logs for troubleshooting
    - Enable Sentry error tracking for production monitoring
    """)


def render_help_center() -> None:
    """Render the main help center interface."""
    st.header("📖 Help Center")
    
    help_tab1, help_tab2, help_tab3, help_tab4 = st.tabs([
        "Quick Start",
        "FAQ",
        "Features",
        "Documentation"
    ])
    
    with help_tab1:
        render_quick_start_guide()
    
    with help_tab2:
        render_faq()
    
    with help_tab3:
        render_key_features()
    
    with help_tab4:
        render_documentation_links()

