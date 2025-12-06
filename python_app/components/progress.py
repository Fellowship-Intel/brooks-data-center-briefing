"""
Progress tracking component for Streamlit.

Provides granular progress indicators for long-running operations like report generation.
"""

import streamlit as st
import time
from typing import List, Optional
from datetime import datetime, timedelta


class ProgressTracker:
    """
    Tracks and displays progress for multi-step operations.
    
    Provides:
    - Step-by-step progress indicators
    - Estimated time remaining (ETA)
    - Current step status
    - Error handling
    """
    
    def __init__(self, steps: List[str], show_eta: bool = True):
        """
        Initialize progress tracker.
        
        Args:
            steps: List of step names
            show_eta: Whether to show estimated time remaining
        """
        self.steps = steps
        self.show_eta = show_eta
        self.current_step = 0
        self.start_time = time.time()
        self.step_times: List[float] = []
        
        # Create UI elements
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        self.eta_text = st.empty() if show_eta else None
        self.steps_container = st.container()
        
        # Display step list
        with self.steps_container:
            self.step_indicators = []
            for i, step in enumerate(steps):
                col1, col2 = st.columns([1, 10])
                with col1:
                    indicator = st.empty()
                with col2:
                    st.caption(step)
                self.step_indicators.append(indicator)
    
    def update(self, step_index: int, message: str, progress: float) -> None:
        """
        Update progress to a specific step.
        
        Args:
            step_index: Index of current step (0-based)
            message: Status message to display
            progress: Progress value (0.0 to 1.0) for current step
        """
        if step_index < 0 or step_index >= len(self.steps):
            return
        
        self.current_step = step_index
        step_progress = (step_index + progress) / len(self.steps)
        
        # Update progress bar
        self.progress_bar.progress(step_progress)
        
        # Update status text
        self.status_text.text(f"📊 {message}")
        
        # Update step indicators
        for i, indicator in enumerate(self.step_indicators):
            if i < step_index:
                indicator.markdown("✅")
            elif i == step_index:
                indicator.markdown("🔄")
            else:
                indicator.markdown("⏳")
        
        # Update ETA
        if self.show_eta and self.eta_text:
            elapsed = time.time() - self.start_time
            if step_progress > 0:
                estimated_total = elapsed / step_progress
                remaining = estimated_total - elapsed
                eta_seconds = int(remaining)
                
                if eta_seconds < 60:
                    eta_str = f"{eta_seconds}s"
                elif eta_seconds < 3600:
                    eta_str = f"{eta_seconds // 60}m {eta_seconds % 60}s"
                else:
                    hours = eta_seconds // 3600
                    minutes = (eta_seconds % 3600) // 60
                    eta_str = f"{hours}h {minutes}m"
                
                self.eta_text.caption(f"⏱️ Estimated time remaining: {eta_str}")
    
    def complete(self, message: str = "✅ Complete!") -> None:
        """Mark all steps as complete."""
        self.progress_bar.progress(1.0)
        self.status_text.text(message)
        
        # Mark all steps as complete
        for indicator in self.step_indicators:
            indicator.markdown("✅")
        
        if self.eta_text:
            elapsed = time.time() - self.start_time
            self.eta_text.caption(f"⏱️ Completed in {elapsed:.1f}s")
    
    def error(self, message: str) -> None:
        """Display error message."""
        self.status_text.error(f"❌ {message}")
        if self.current_step < len(self.step_indicators):
            self.step_indicators[self.current_step].markdown("❌")


def create_progress_tracker(steps: List[str], show_eta: bool = True) -> ProgressTracker:
    """
    Create a progress tracker for multi-step operations.
    
    Args:
        steps: List of step names
        show_eta: Whether to show estimated time remaining
        
    Returns:
        ProgressTracker instance
        
    Example:
        tracker = create_progress_tracker(["Step 1", "Step 2", "Step 3"])
        tracker.update(0, "Processing...", 0.5)
        tracker.update(1, "Almost done...", 0.8)
        tracker.complete("Done!")
    """
    return ProgressTracker(steps, show_eta)
