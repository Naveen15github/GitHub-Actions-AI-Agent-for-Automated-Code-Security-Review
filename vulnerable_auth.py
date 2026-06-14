"""
Authentication module with intentional security vulnerabilities
for testing AI code review agent
"""

import sqlite3
import hashlib
import os

# SECURITY ISSUE: Hardcoded credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123456"
API_SECRET_KEY = "sk-prod-a1b2c3d4e5f6g7h8i9j0"
DATABASE_PASSWORD = "MyS3cr3tP@ssw0rd!"


def authenticate_user(username, password):
    """
    VULNERABILITY: SQL Injection
    User input is directly interpolated into SQL query
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Dangerous SQL query - allows SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    return result is not None


def get_user_profile(user_id):
    """
    VULNERABILITY: SQL Injection via format string
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Another SQL injection point
    cursor.execute(f"SELECT * FROM profiles WHERE user_id = {user_id}")
    profile = cursor.fetchone()
    conn.close()
    return profile


def reset_password(email, new_password):
    """
    VULNERABILITY: No input validation
    VULNERABILITY: Password stored in plaintext
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # No validation on email format
    # No password complexity requirements
    # Password stored without hashing
    cursor.execute(f"UPDATE users SET password = '{new_password}' WHERE email = '{email}'")
    conn.commit()
    conn.close()
    return True


def execute_admin_command(command):
    """
    CRITICAL VULNERABILITY: Command Injection
    Allows arbitrary system command execution
    """
    # Directly executing user input as system command
    result = os.system(command)
    return result


def generate_auth_token(user_id):
    """
    VULNERABILITY: Weak cryptography
    Using MD5 which is cryptographically broken
    """
    # MD5 is deprecated and insecure
    token = hashlib.md5(str(user_id).encode()).hexdigest()
    return token


class UserSession:
    """
    VULNERABILITY: Insecure session management
    """
    def __init__(self, user_id):
        self.user_id = user_id
        # ISSUE: Session token is predictable
        self.session_token = f"session_{user_id}_{12345}"
        # ISSUE: No expiration time
        self.created_at = None
        
    def validate(self):
        # ISSUE: No actual validation logic
        return True


# VULNERABILITY: Debug mode enabled in production
DEBUG_MODE = True
if DEBUG_MODE:
    # Exposing sensitive information
    print(f"Admin credentials: {ADMIN_USERNAME}:{ADMIN_PASSWORD}")
    print(f"API Key: {API_SECRET_KEY}")
