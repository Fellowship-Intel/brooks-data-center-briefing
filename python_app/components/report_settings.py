"""
Report settings and customization component.

Provides section toggles, detail level control, and template management.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from report_repository import get_client, create_or_update_client


class ReportSettings:
    """Report generation settings and preferences."""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load settings from Firestore or use defaults."""
        try:
            client = get_client(self.client_id)
            if client and "report_settings" in client:
                settings = client["report_settings"]
                self.show_summary = settings.get("show_summary", True)
                self.show_key_insights = settings.get("show_key_insights", True)
                self.show_market_context = settings.get("show_market_context", True)
                self.show_audio_report = settings.get("show_audio_report", True)
                self.show_top_movers = settings.get("show_top_movers", True)
                self.show_deep_dive = settings.get("show_deep_dive", True)
                self.show_full_narrative = settings.get("show_full_narrative", True)
                self.detail_level = settings.get("detail_level", "standard")  # minimal, standard, detailed
                self.template_name = settings.get("template_name", "default")
            else:
                # Default settings
                self.show_summary = True
                self.show_key_insights = True
                self.show_market_context = True
                self.show_audio_report = True
                self.show_top_movers = True
                self.show_deep_dive = True
                self.show_full_narrative = True
                self.detail_level = "standard"
                self.template_name = "default"
        except Exception:
            # Use defaults if loading fails
            self.show_summary = True
            self.show_key_insights = True
            self.show_market_context = True
            self.show_audio_report = True
            self.show_top_movers = True
            self.show_deep_dive = True
            self.show_full_narrative = True
            self.detail_level = "standard"
            self.template_name = "default"
    
    def save(self) -> bool:
        """Save settings to Firestore."""
        try:
            client = get_client(self.client_id)
            settings = {
                "show_summary": self.show_summary,
                "show_key_insights": self.show_key_insights,
                "show_market_context": self.show_market_context,
                "show_audio_report": self.show_audio_report,
                "show_top_movers": self.show_top_movers,
                "show_deep_dive": self.show_deep_dive,
                "show_full_narrative": self.show_full_narrative,
                "detail_level": self.detail_level,
                "template_name": self.template_name,
            }
            
            if client:
                client["report_settings"] = settings
                create_or_update_client(self.client_id, **client)
            else:
                create_or_update_client(
                    self.client_id,
                    report_settings=settings
                )
            return True
        except Exception as e:
            st.error(f"Failed to save settings: {str(e)}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "show_summary": self.show_summary,
            "show_key_insights": self.show_key_insights,
            "show_market_context": self.show_market_context,
            "show_audio_report": self.show_audio_report,
            "show_top_movers": self.show_top_movers,
            "show_deep_dive": self.show_deep_dive,
            "show_full_narrative": self.show_full_narrative,
            "detail_level": self.detail_level,
            "template_name": self.template_name,
        }


def render_report_settings(client_id: str) -> None:
    """
    Render report settings UI.
    
    Args:
        client_id: Client ID
    """
    st.subheader("⚙️ Report Settings")
    
    settings = ReportSettings(client_id)
    
    # Section toggles
    st.markdown("**Display Sections**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        settings.show_summary = st.checkbox("Summary", value=settings.show_summary, key="setting_summary")
        settings.show_key_insights = st.checkbox("Key Insights", value=settings.show_key_insights, key="setting_insights")
        settings.show_market_context = st.checkbox("Market Context", value=settings.show_market_context, key="setting_context")
        settings.show_audio_report = st.checkbox("Audio Report", value=settings.show_audio_report, key="setting_audio")
    
    with col2:
        settings.show_top_movers = st.checkbox("Top Movers", value=settings.show_top_movers, key="setting_movers")
        settings.show_deep_dive = st.checkbox("Deep Dive", value=settings.show_deep_dive, key="setting_deep")
        settings.show_full_narrative = st.checkbox("Full Narrative", value=settings.show_full_narrative, key="setting_narrative")
    
    st.divider()
    
    # Detail level
    st.markdown("**Detail Level**")
    detail_level = st.radio(
        "Report Detail Level",
        options=["minimal", "standard", "detailed"],
        index=["minimal", "standard", "detailed"].index(settings.detail_level),
        key="setting_detail_level",
        help="Controls the depth of analysis in reports"
    )
    settings.detail_level = detail_level
    
    st.divider()
    
    # Templates
    st.markdown("**Report Templates**")
    templates = {
        "default": "Standard daily briefing",
        "quick": "Quick summary only",
        "comprehensive": "Full detailed analysis",
        "trading_focused": "Trading-specific insights",
    }
    
    selected_template = st.selectbox(
        "Template",
        options=list(templates.keys()),
        index=list(templates.keys()).index(settings.template_name) if settings.template_name in templates else 0,
        format_func=lambda x: f"{x.title()}: {templates[x]}",
        key="setting_template"
    )
    settings.template_name = selected_template
    
    # Save button
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        if settings.save():
            st.success("Settings saved successfully!")
        else:
            st.error("Failed to save settings")
    
    # Reset to defaults
    if st.button("🔄 Reset to Defaults", use_container_width=True):
        settings.show_summary = True
        settings.show_key_insights = True
        settings.show_market_context = True
        settings.show_audio_report = True
        settings.show_top_movers = True
        settings.show_deep_dive = True
        settings.show_full_narrative = True
        settings.detail_level = "standard"
        settings.template_name = "default"
        if settings.save():
            st.success("Settings reset to defaults!")
            st.rerun()


def get_report_settings(client_id: str) -> ReportSettings:
    """
    Get report settings for a client.
    
    Args:
        client_id: Client ID
        
    Returns:
        ReportSettings instance
    """
    return ReportSettings(client_id)

