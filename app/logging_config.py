import logging
import json
from typing import Any
from datetime import datetime

class GoogleCloudFormatter(logging.Formatter):
    """
    JSON formatter compatible with Google Cloud Logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Build the message payload
        message = record.getMessage()
        
        # Standard Cloud Logging fields
        log_entry = {
            "message": message,
            "severity": record.levelname,
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "component": record.name,
            # Add trace info if available (can be enhanced with OpenTelemetry later)
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }
        }

        # Handle exception info
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            # Or use stack_trace for full rendering in GCP
            # log_entry["stack_trace"] = ... 

        # Merge any extra attributes passed (structLog style) if they are json serializable
        # NOTE: In standard python logging, extra={...} puts keys in record.__dict__
        # We handle known extras but robust generic merging is tricky with standard logging.
        # For simple usage, we stick to message.
        
        return json.dumps(log_entry)

def configure_logging(level: str = "INFO"):
    """
    Configure root logger to use JSON formatting.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Create console handler with JSON formatter
    handler = logging.StreamHandler()
    handler.setFormatter(GoogleCloudFormatter())
    root_logger.addHandler(handler)
    
    # Set levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Reduce access logs if needed
