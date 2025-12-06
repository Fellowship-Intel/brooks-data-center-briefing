# Streamlit Components

This directory contains reusable Streamlit UI components for the Brooks Data Center Daily Briefing application.

## Components

### Progress Tracker (`progress.py`)

A comprehensive progress tracking component for long-running operations like report generation.

**Features:**
- Step-by-step progress indicators with visual status (✅, 🔄, ⏳)
- Estimated time remaining (ETA) calculation
- Error handling with visual feedback
- Progress bar with percentage completion

**Usage:**
```python
from python_app.components.progress import create_progress_tracker

steps = [
    "Rate limit check",
    "Fetching market data",
    "Generating AI report text",
    "Storing report in Firestore",
    "Generating audio (TTS)",
    "Uploading audio to Cloud Storage",
    "Finalizing report"
]
tracker = create_progress_tracker(steps, show_eta=True)

# Update progress
tracker.update(0, "Checking rate limits...", 0.05)
tracker.update(1, "Fetching market data...", 0.15)
# ... continue updating

# Complete
tracker.complete("Report generated successfully!")

# Or handle errors
tracker.error("Rate limit exceeded")
```

**API:**
- `create_progress_tracker(steps: List[str], show_eta: bool = True) -> ProgressTracker`
- `ProgressTracker.update(step_index: int, message: str, progress: float) -> None`
- `ProgressTracker.complete(message: str = "✅ Complete!") -> None`
- `ProgressTracker.error(message: str) -> None`

### Keyboard Shortcuts (`keyboard_shortcuts.py`)

Keyboard shortcuts documentation and help system for desktop users.

**Features:**
- Help dialog showing available keyboard shortcuts
- Shortcut definitions for common actions
- JavaScript infrastructure for future implementation

**Available Shortcuts:**
- `1-4`: Navigate between tabs (Dashboard, Watchlist Report, Report History, AI Chat)
- `G`: Generate report (when on Dashboard)
- `R`: Refresh data
- `?`: Show keyboard shortcuts help
- `Esc`: Close dialogs/modals

**Usage:**
```python
from python_app.components.keyboard_shortcuts import render_keyboard_shortcuts_help

# In sidebar or help section
render_keyboard_shortcuts_help()
```

**API:**
- `render_keyboard_shortcuts_help() -> None`: Render help dialog
- `get_shortcut_description(key: str) -> Optional[str]`: Get description for a shortcut

### Status Indicators (`status_indicators.py`)

System health status indicators showing the status of various services.

**Features:**
- Live system health checks
- Service status badges
- Refresh functionality

**Usage:**
```python
from python_app.components.status_indicators import render_status_indicators

# In sidebar
render_status_indicators(show_in_sidebar=True)

# Or in main area
render_status_indicators(show_in_sidebar=False)
```

### Dashboard (`dashboard.py`)

Main dashboard component displaying key metrics and recent activity.

**Features:**
- Key metrics (total reports, TTS success rate, etc.)
- Recent activity timeline
- System health status

**Usage:**
```python
from python_app.components.dashboard import render_dashboard
from gcp_clients import get_firestore_client

firestore_client = get_firestore_client()
render_dashboard(firestore_client, client_id="michael_brooks")
```

## Testing

All components have corresponding test files in the `tests/` directory:
- `tests/test_progress_tracker.py` - Progress tracker tests
- `tests/test_keyboard_shortcuts.py` - Keyboard shortcuts tests

Run tests with:
```bash
pytest tests/test_progress_tracker.py -v
pytest tests/test_keyboard_shortcuts.py -v
```

## Contributing

When adding new components:
1. Create the component file in this directory
2. Add comprehensive docstrings
3. Create corresponding test file in `tests/`
4. Update this README with component documentation
5. Add usage examples

