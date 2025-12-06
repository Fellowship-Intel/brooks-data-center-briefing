"""
Input validation and sanitization utilities.

Provides validation and sanitization functions for user inputs to prevent
injection attacks, XSS, and other security vulnerabilities.
"""

import re
import html
from typing import Any, Dict, List, Optional
from datetime import date, datetime
from utils.exceptions import ValidationError


# Ticker symbol validation pattern (uppercase letters, 1-5 characters)
TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')

# Client ID validation pattern (alphanumeric, underscore, hyphen, 3-50 chars)
CLIENT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')

# Maximum lengths
MAX_CLIENT_ID_LENGTH = 50
MAX_TICKER_LENGTH = 5
MAX_WATCHLIST_SIZE = 100
MAX_TEXT_LENGTH = 10000
MAX_JSON_DEPTH = 10


def validate_ticker(ticker: str) -> str:
    """
    Validate and sanitize a ticker symbol.
    
    Args:
        ticker: Ticker symbol to validate
        
    Returns:
        Uppercase, validated ticker symbol
        
    Raises:
        ValidationError: If ticker is invalid
    """
    if not ticker:
        raise ValidationError("Ticker symbol cannot be empty")
    
    # Strip whitespace and convert to uppercase
    ticker = ticker.strip().upper()
    
    if len(ticker) > MAX_TICKER_LENGTH:
        raise ValidationError(f"Ticker symbol too long (max {MAX_TICKER_LENGTH} characters)")
    
    if not TICKER_PATTERN.match(ticker):
        raise ValidationError(
            f"Invalid ticker symbol format: {ticker}. "
            "Ticker must be 1-5 uppercase letters."
        )
    
    return ticker


def validate_ticker_list(tickers: List[str]) -> List[str]:
    """
    Validate and sanitize a list of ticker symbols.
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        List of validated, uppercase ticker symbols
        
    Raises:
        ValidationError: If any ticker is invalid or list is too large
    """
    if not tickers:
        return []
    
    if len(tickers) > MAX_WATCHLIST_SIZE:
        raise ValidationError(f"Watchlist too large (max {MAX_WATCHLIST_SIZE} tickers)")
    
    validated = []
    seen = set()
    
    for ticker in tickers:
        validated_ticker = validate_ticker(ticker)
        
        # Check for duplicates
        if validated_ticker in seen:
            continue  # Skip duplicates
        
        seen.add(validated_ticker)
        validated.append(validated_ticker)
    
    return validated


def validate_client_id(client_id: str) -> str:
    """
    Validate and sanitize a client ID.
    
    Args:
        client_id: Client ID to validate
        
    Returns:
        Validated client ID
        
    Raises:
        ValidationError: If client_id is invalid
    """
    if not client_id:
        raise ValidationError("Client ID cannot be empty")
    
    client_id = client_id.strip()
    
    if len(client_id) > MAX_CLIENT_ID_LENGTH:
        raise ValidationError(f"Client ID too long (max {MAX_CLIENT_ID_LENGTH} characters)")
    
    if not CLIENT_ID_PATTERN.match(client_id):
        raise ValidationError(
            f"Invalid client ID format: {client_id}. "
            "Client ID must be 3-50 alphanumeric characters, underscores, or hyphens."
        )
    
    return client_id


def validate_trading_date(trading_date: Any) -> date:
    """
    Validate a trading date.
    
    Args:
        trading_date: Date object or ISO date string
        
    Returns:
        Validated date object
        
    Raises:
        ValidationError: If date is invalid
    """
    if isinstance(trading_date, date):
        return trading_date
    
    if isinstance(trading_date, datetime):
        return trading_date.date()
    
    if isinstance(trading_date, str):
        try:
            return date.fromisoformat(trading_date)
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {trading_date}. Use YYYY-MM-DD format.") from e
    
    raise ValidationError(f"Invalid date type: {type(trading_date)}")


def sanitize_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """
    Sanitize text input by escaping HTML and limiting length.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Escape HTML to prevent XSS
    text = html.escape(text)
    
    return text


def validate_json_structure(
    data: Any,
    max_depth: int = MAX_JSON_DEPTH,
    current_depth: int = 0
) -> None:
    """
    Validate JSON structure to prevent deeply nested objects (DoS protection).
    
    Args:
        data: JSON data to validate
        max_depth: Maximum allowed nesting depth
        current_depth: Current nesting depth (internal use)
        
    Raises:
        ValidationError: If structure is too deeply nested
    """
    if current_depth > max_depth:
        raise ValidationError(f"JSON structure too deeply nested (max {max_depth} levels)")
    
    if isinstance(data, dict):
        for value in data.values():
            validate_json_structure(value, max_depth, current_depth + 1)
    elif isinstance(data, list):
        for item in data:
            validate_json_structure(item, max_depth, current_depth + 1)


def validate_market_data(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize market data structure.
    
    Args:
        market_data: Market data dictionary
        
    Returns:
        Validated market data
        
    Raises:
        ValidationError: If market data is invalid
    """
    if not isinstance(market_data, dict):
        raise ValidationError("Market data must be a dictionary")
    
    # Validate structure depth
    validate_json_structure(market_data)
    
    # Validate tickers if present
    if "tickers" in market_data:
        if isinstance(market_data["tickers"], list):
            market_data["tickers"] = validate_ticker_list(market_data["tickers"])
        else:
            raise ValidationError("Market data 'tickers' must be a list")
    
    # Validate prices if present
    if "prices" in market_data:
        if not isinstance(market_data["prices"], dict):
            raise ValidationError("Market data 'prices' must be a dictionary")
        
        # Validate price keys are valid tickers
        for ticker in market_data["prices"].keys():
            validate_ticker(ticker)
    
    return market_data


def validate_watchlist_request(
    client_id: str,
    watchlist: List[str],
    trading_date: Optional[date] = None
) -> tuple[str, List[str], date]:
    """
    Validate a watchlist report request.
    
    Args:
        client_id: Client ID
        watchlist: List of ticker symbols
        trading_date: Optional trading date
        
    Returns:
        Tuple of (validated_client_id, validated_watchlist, validated_date)
        
    Raises:
        ValidationError: If any field is invalid
    """
    validated_client_id = validate_client_id(client_id)
    validated_watchlist = validate_ticker_list(watchlist)
    
    if trading_date:
        validated_date = validate_trading_date(trading_date)
    else:
        validated_date = date.today()
    
    return validated_client_id, validated_watchlist, validated_date

