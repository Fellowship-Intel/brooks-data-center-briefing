"""Enhanced JSON parsing with robust error handling."""
import json
import re
from typing import Any, Dict, Optional


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text that may contain markdown or extra text.
    Handles common edge cases.
    
    Args:
        text: Text that may contain JSON, possibly wrapped in markdown
        
    Returns:
        Parsed JSON dictionary, or None if extraction fails
    """
    if not text:
        return None
    
    # Remove markdown code fences
    text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```\s*', '', text)
    
    # Find JSON object boundaries
    start = text.find('{')
    end = text.rfind('}')
    
    if start == -1 or end == -1 or end <= start:
        return None
    
    json_str = text[start:end + 1]
    
    # Try to parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Try to fix common issues
        json_str = fix_common_json_issues(json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None


def fix_common_json_issues(json_str: str) -> str:
    """
    Fix common JSON formatting issues.
    
    Args:
        json_str: JSON string that may have formatting issues
        
    Returns:
        Fixed JSON string
    """
    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # Fix unescaped newlines in strings (basic attempt)
    # This is conservative - only fixes obvious cases
    json_str = re.sub(r'(?<!\\)\n(?![\\"])', '\\n', json_str)
    
    return json_str


def parse_gemini_json_response(text: str) -> Dict[str, Any]:
    """
    Parse JSON from Gemini response with robust error handling.
    Raises RuntimeError if parsing fails.
    
    Args:
        text: Response text from Gemini
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        RuntimeError: If JSON cannot be extracted or parsed
    """
    if not text:
        raise RuntimeError("Empty response text")
    
    parsed = extract_json_from_text(text)
    
    if parsed is None:
        # Log the problematic text for debugging
        snippet = text[:500] if len(text) > 500 else text
        raise RuntimeError(
            f"Could not extract valid JSON from response. "
            f"Response snippet: {snippet}"
        )
    
    return parsed

