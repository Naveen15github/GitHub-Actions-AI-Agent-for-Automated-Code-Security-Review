"""
String utility functions - secure and well-written code
for testing AI code review agent (low-risk scenario)
"""

from typing import Optional, List
import re


def capitalize_words(text: str) -> str:
    """
    Capitalize the first letter of each word in a string.
    
    Args:
        text: Input string to capitalize
        
    Returns:
        String with each word capitalized
        
    Example:
        >>> capitalize_words("hello world")
        "Hello World"
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    return text.title()


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length, adding a suffix if truncated.
    
    Args:
        text: String to truncate
        max_length: Maximum length of the output string
        suffix: Suffix to add if truncated (default: "...")
        
    Returns:
        Truncated string with suffix if needed
        
    Example:
        >>> truncate_string("This is a long text", 10)
        "This is..."
    """
    if not isinstance(text, str):
        raise TypeError("Text must be a string")
    
    if not isinstance(max_length, int) or max_length < 0:
        raise ValueError("max_length must be a positive integer")
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Remove or replace characters that are invalid in filenames.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem use
        
    Example:
        >>> sanitize_filename("my/file:name*.txt")
        "my_file_name_.txt"
    """
    if not isinstance(filename, str):
        raise TypeError("Filename must be a string")
    
    # Replace invalid characters with underscore
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    
    return sanitized if sanitized else "unnamed"


def count_words(text: str) -> int:
    """
    Count the number of words in a string.
    
    Args:
        text: Input string
        
    Returns:
        Number of words
        
    Example:
        >>> count_words("Hello world, how are you?")
        5
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    # Split by whitespace and filter empty strings
    words = [word for word in text.split() if word]
    return len(words)


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from a string.
    
    Args:
        text: Text containing potential email addresses
        
    Returns:
        List of found email addresses
        
    Example:
        >>> extract_emails("Contact us at info@example.com or support@test.org")
        ['info@example.com', 'support@test.org']
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    # Basic email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    return list(set(emails))  # Remove duplicates
