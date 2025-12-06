"""
Tests for the progress tracker component.

Tests the ProgressTracker class and create_progress_tracker function.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from python_app.components.progress import ProgressTracker, create_progress_tracker


class TestProgressTracker:
    """Test the ProgressTracker class."""
    
    def test_initialization(self):
        """Test that ProgressTracker initializes correctly."""
        steps = ["Step 1", "Step 2", "Step 3"]
        
        with patch('streamlit.progress'), \
             patch('streamlit.empty'), \
             patch('streamlit.container'), \
             patch('streamlit.columns'), \
             patch('streamlit.caption'):
            
            tracker = ProgressTracker(steps, show_eta=True)
            
            assert tracker.steps == steps
            assert tracker.show_eta is True
            assert tracker.current_step == 0
            assert tracker.start_time > 0
            assert len(tracker.step_indicators) == 3
    
    def test_initialization_without_eta(self):
        """Test initialization without ETA display."""
        steps = ["Step 1", "Step 2"]
        
        with patch('streamlit.progress'), \
             patch('streamlit.empty'), \
             patch('streamlit.container'), \
             patch('streamlit.columns'), \
             patch('streamlit.caption'):
            
            tracker = ProgressTracker(steps, show_eta=False)
            
            assert tracker.show_eta is False
            assert tracker.eta_text is None
    
    def test_update_progress(self):
        """Test updating progress."""
        steps = ["Step 1", "Step 2", "Step 3"]
        
        with patch('streamlit.progress') as mock_progress, \
             patch('streamlit.empty') as mock_empty, \
             patch('streamlit.container'), \
             patch('streamlit.columns'), \
             patch('streamlit.caption'):
            
            mock_progress_bar = MagicMock()
            mock_progress.return_value = mock_progress_bar
            
            mock_status = MagicMock()
            mock_eta = MagicMock()
            mock_empty.side_effect = [mock_status, mock_eta]
            
            tracker = ProgressTracker(steps, show_eta=True)
            
            # Update to step 0 with 50% progress
            tracker.update(0, "Processing...", 0.5)
            
            # Check that progress bar was updated
            assert mock_progress_bar.progress.called
            call_args = mock_progress_bar.progress.call_args[0][0]
            assert 0 < call_args < 1  # Should be between 0 and 1
            
            # Check that status text was updated
            assert mock_status.text.called
    
    def test_update_invalid_step(self):
        """Test that invalid step indices are ignored."""
        steps = ["Step 1", "Step 2"]
        
        with patch('streamlit.progress'), \
             patch('streamlit.empty'), \
             patch('streamlit.container'), \
             patch('streamlit.columns'), \
             patch('streamlit.caption'):
            
            tracker = ProgressTracker(steps, show_eta=False)
            
            # Try to update with invalid step indices
            tracker.update(-1, "Invalid", 0.5)  # Should be ignored
            tracker.update(10, "Invalid", 0.5)  # Should be ignored
            
            # Should not raise an error
            assert tracker.current_step == 0
    
    def test_complete(self):
        """Test marking progress as complete."""
        steps = ["Step 1", "Step 2"]
        
        with patch('streamlit.progress') as mock_progress, \
             patch('streamlit.empty') as mock_empty, \
             patch('streamlit.container'), \
             patch('streamlit.columns'), \
             patch('streamlit.caption'):
            
            mock_progress_bar = MagicMock()
            mock_progress.return_value = mock_progress_bar
            
            mock_status = MagicMock()
            mock_eta = MagicMock()
            mock_empty.side_effect = [mock_status, mock_eta]
            
            tracker = ProgressTracker(steps, show_eta=True)
            tracker.complete("Done!")
            
            # Check that progress bar was set to 1.0
            mock_progress_bar.progress.assert_called_with(1.0)
            
            # Check that status text was updated
            mock_status.text.assert_called_with("Done!")
    
    def test_error(self):
        """Test error handling."""
        steps = ["Step 1", "Step 2"]
        
        with patch('streamlit.progress'), \
             patch('streamlit.empty') as mock_empty, \
             patch('streamlit.container'), \
             patch('streamlit.columns'), \
             patch('streamlit.caption'):
            
            mock_status = MagicMock()
            mock_empty.return_value = mock_status
            
            tracker = ProgressTracker(steps, show_eta=False)
            tracker.current_step = 0
            tracker.error("Something went wrong")
            
            # Check that error was displayed
            mock_status.error.assert_called()
    
    def test_eta_calculation(self):
        """Test ETA calculation logic."""
        steps = ["Step 1", "Step 2", "Step 3"]
        
        with patch('streamlit.progress'), \
             patch('streamlit.empty') as mock_empty, \
             patch('streamlit.container'), \
             patch('streamlit.columns'), \
             patch('streamlit.caption'):
            
            mock_status = MagicMock()
            mock_eta = MagicMock()
            mock_empty.side_effect = [mock_status, mock_eta]
            
            tracker = ProgressTracker(steps, show_eta=True)
            
            # Simulate some elapsed time
            time.sleep(0.1)
            
            # Update progress
            tracker.update(1, "Halfway", 0.5)
            
            # Check that ETA was calculated and displayed
            assert mock_eta.caption.called


class TestCreateProgressTracker:
    """Test the create_progress_tracker factory function."""
    
    def test_create_tracker(self):
        """Test creating a progress tracker."""
        steps = ["Step 1", "Step 2"]
        
        with patch('python_app.components.progress.ProgressTracker') as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker_class.return_value = mock_tracker
            
            result = create_progress_tracker(steps, show_eta=True)
            
            assert result == mock_tracker
            mock_tracker_class.assert_called_once_with(steps, show_eta=True)
    
    def test_create_tracker_default_eta(self):
        """Test creating tracker with default ETA setting."""
        steps = ["Step 1"]
        
        with patch('python_app.components.progress.ProgressTracker') as mock_tracker_class:
            create_progress_tracker(steps)
            
            # Should default to show_eta=True
            mock_tracker_class.assert_called_once_with(steps, show_eta=True)

