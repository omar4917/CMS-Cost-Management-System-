"""
Authentication module for CMS Desktop App.
Handles login verification directly against MySQL.
"""

import bcrypt
from core.database import execute_query


def verify_login(username, password):
    """Verify admin login credentials."""
    users = execute_query(
        "SELECT id, username, email, password, first_name, last_name, role, is_active "
        "FROM users WHERE username = %s AND is_active = 1",
        (username,)
    )
    if not users:
        return None, "Invalid username or password"
    
    user = users[0]
    stored_hash = user['password']
    
    # bcryptjs (Node.js) uses $2a$ prefix, Python bcrypt uses $2b$
    # They are compatible — just need to handle encoding
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    if bcrypt.checkpw(password, stored_hash):
        # Log the login
        execute_query(
            "INSERT INTO audit_logs (user_id, action, description, ip_address, created_at) "
            "VALUES (%s, 'login', %s, 'desktop-app', NOW())",
            (user['id'], f"User {user['username']} logged in via desktop app"),
            fetch=False
        )
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'firstName': user['first_name'],
            'lastName': user['last_name'],
            'role': user['role'],
        }, None
    
    return None, "Invalid username or password"
