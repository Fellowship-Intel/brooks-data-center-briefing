"""Custom exception classes for the application."""
from typing import Optional, Dict, Any


class ReportGenerationError(Exception):
    """Raised when report generation fails."""
    
    def __init__(
        self,
        message: str,
        client_id: Optional[str] = None,
        trading_date: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize report generation error.
        
        Args:
            message: Error message
            client_id: Client ID associated with the error
            trading_date: Trading date associated with the error
            context: Additional context dictionary
        """
        super().__init__(message)
        self.client_id = client_id
        self.trading_date = trading_date
        self.context = context or {}
    
    def __str__(self) -> str:
        """Format error message with context."""
        parts = [super().__str__()]
        if self.client_id:
            parts.append(f"client_id={self.client_id}")
        if self.trading_date:
            parts.append(f"trading_date={self.trading_date}")
        return " | ".join(parts)


class TTSGenerationError(Exception):
    """Raised when TTS generation fails."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        text_length: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize TTS generation error.
        
        Args:
            message: Error message
            provider: TTS provider name (e.g., 'eleven_labs', 'gemini')
            text_length: Length of text that failed to convert
            context: Additional context dictionary
        """
        super().__init__(message)
        self.provider = provider
        self.text_length = text_length
        self.context = context or {}
    
    def __str__(self) -> str:
        """Format error message with context."""
        parts = [super().__str__()]
        if self.provider:
            parts.append(f"provider={self.provider}")
        if self.text_length:
            parts.append(f"text_length={self.text_length}")
        return " | ".join(parts)


class StorageError(Exception):
    """Raised when storage operations (GCS/Firestore) fail."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        resource: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize storage error.
        
        Args:
            message: Error message
            operation: Operation that failed (e.g., 'upload', 'download', 'write')
            resource: Resource identifier (e.g., GCS path, Firestore document ID)
            context: Additional context dictionary
        """
        super().__init__(message)
        self.operation = operation
        self.resource = resource
        self.context = context or {}
    
    def __str__(self) -> str:
        """Format error message with context."""
        parts = [super().__str__()]
        if self.operation:
            parts.append(f"operation={self.operation}")
        if self.resource:
            parts.append(f"resource={self.resource}")
        return " | ".join(parts)


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    
    def __init__(
        self,
        message: str,
        missing_keys: Optional[list] = None,
        invalid_values: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            missing_keys: List of missing configuration keys
            invalid_values: Dictionary of invalid configuration values
        """
        super().__init__(message)
        self.missing_keys = missing_keys or []
        self.invalid_values = invalid_values or {}
    
    def __str__(self) -> str:
        """Format error message with context."""
        parts = [super().__str__()]
        if self.missing_keys:
            parts.append(f"missing_keys={self.missing_keys}")
        if self.invalid_values:
            parts.append(f"invalid_values={self.invalid_values}")
        return " | ".join(parts)


class APIError(Exception):
    """Raised when external API calls fail."""
    
    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response: Optional[str] = None,
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            api_name: Name of the API (e.g., 'gemini', 'eleven_labs')
            status_code: HTTP status code if applicable
            response: API response body if available
        """
        super().__init__(message)
        self.api_name = api_name
        self.status_code = status_code
        self.response = response
    
    def __str__(self) -> str:
        """Format error message with context."""
        parts = [super().__str__()]
        if self.api_name:
            parts.append(f"api={self.api_name}")
        if self.status_code:
            parts.append(f"status={self.status_code}")
        return " | ".join(parts)


class ValidationError(Exception):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that failed validation
            value: Value that failed validation
        """
        super().__init__(message)
        self.field = field
        self.value = value
    
    def __str__(self) -> str:
        """Format error message with context."""
        parts = [super().__str__()]
        if self.field:
            parts.append(f"field={self.field}")
        return " | ".join(parts)
