"""
Tests for the keyboard shortcuts component.

Tests the keyboard shortcuts module functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from python_app.components.keyboard_shortcuts import (
    render_keyboard_shortcuts_help,
    get_shortcut_description,
    _SHORTCUTS
)


class TestKeyboardShortcuts:
    """Test keyboard shortcuts functionality."""
    
    def test_get_shortcut_description_valid(self):
        """Test getting description for valid shortcuts."""
        assert get_shortcut_description("g") == "Generate report"
        assert get_shortcut_description("r") == "Refresh data"
        assert get_shortcut_description("1") == "Switch to Dashboard tab"
        assert get_shortcut_description("?") == "Show keyboard shortcuts"
        assert get_shortcut_description("Escape") == "Close dialogs/modals"
    
    def test_get_shortcut_description_invalid(self):
        """Test getting description for invalid shortcuts."""
        assert get_shortcut_description("invalid") is None
        assert get_shortcut_description("") is None
        assert get_shortcut_description("xyz") is None
    
    def test_shortcuts_dict_structure(self):
        """Test that shortcuts dictionary has correct structure."""
        for key, info in _SHORTCUTS.items():
            assert "description" in info
            assert "action" in info
            assert "key" in info
            assert isinstance(info["description"], str)
            assert isinstance(info["action"], str)
            assert isinstance(info["key"], str)
    
    def test_render_keyboard_shortcuts_help(self):
        """Test rendering keyboard shortcuts help."""
        with patch('streamlit.expander') as mock_expander, \
             patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.dataframe') as mock_dataframe, \
             patch('pandas.DataFrame') as mock_pd:
            
            mock_expander_context = MagicMock()
            mock_expander.return_value.__enter__.return_value = mock_expander_context
            mock_expander.return_value.__exit__.return_value = None
            
            render_keyboard_shortcuts_help()
            
            # Check that expander was created
            assert mock_expander.called
            
            # Check that markdown was called (for help text)
            assert mock_markdown.called
    
    def test_all_shortcuts_have_descriptions(self):
        """Test that all shortcuts have non-empty descriptions."""
        for key, info in _SHORTCUTS.items():
            assert info["description"], f"Shortcut '{key}' has empty description"
            assert len(info["description"]) > 0
    
    def test_shortcut_keys_match(self):
        """Test that shortcut keys in dict match the key."""
        for key, info in _SHORTCUTS.items():
            assert info["key"] == key, f"Key mismatch for shortcut '{key}'"

