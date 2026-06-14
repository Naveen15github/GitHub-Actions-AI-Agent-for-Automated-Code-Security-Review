"""
Test file to demonstrate AI code review capabilities
"""

import sqlite3

def get_user_data(username):
    """Fetch user data - intentionally has SQL injection vulnerability"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Vulnerable SQL query - directly interpolating user input
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    return result


def authenticate(username, password):
    """Authentication function with hardcoded credentials"""
    # Security issue: hardcoded credentials
    ADMIN_PASSWORD = "admin123"
    API_KEY = "sk-1234567890abcdef"
    
    if username == "admin" and password == ADMIN_PASSWORD:
        return True
    return False


def process_payment(amount):
    """Process payment without validation"""
    # Missing input validation
    total = amount * 1.1  # Add 10% tax
    
    # No error handling for negative amounts
    return total
