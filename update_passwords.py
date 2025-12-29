#!/usr/bin/env python3
"""
Script to update user passwords in the QueryAI database.
Run this script to set real passwords for existing users.
"""

import sys
import os

# Add the project root to the path for proper imports
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.db.models import User
from server.auth.authentication import get_password_hash
from shared.config import settings

def update_user_password(username: str, new_password: str):
    """Update password for a specific user."""
    # Use the same database connection as the application
    DATABASE_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find user
        user = session.query(User).filter(User.username == username).first()
        if not user:
            print(f"❌ User '{username}' not found!")
            return False
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        session.commit()
        
        print(f"✅ Password updated for user '{username}' (Role: {user.role})")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error updating password for '{username}': {e}")
        return False
    finally:
        session.close()

def list_users():
    """List all users in the database."""
    DATABASE_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        users = session.query(User).all()
        print("\\n📋 Current Users:")
        print("-" * 50)
        for user in users:
            needs_update = "dummy_hash_replace_later" in user.hashed_password
            status = "🔐 NEEDS PASSWORD" if needs_update else "✅ Password Set"
            print(f"ID: {user.id} | Username: {user.username} | Role: {user.role} | {status}")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        session.close()

def main():
    if len(sys.argv) < 2:
        print("🔐 QueryAI Password Manager")
        print("=" * 40)
        print()
        print("Usage:")
        print("  python update_passwords.py list                    # List all users")
        print("  python update_passwords.py <username> <password>   # Update password")
        print()
        print("Examples:")
        print("  python update_passwords.py list")
        print("  python update_passwords.py admin admin123")
        print("  python update_passwords.py analyst data456")
        print("  python update_passwords.py viewer view789")
        return
    
    if sys.argv[1] == "list":
        list_users()
    elif len(sys.argv) == 3:
        username = sys.argv[1]
        password = sys.argv[2]
        update_user_password(username, password)
    else:
        print("❌ Invalid arguments. Use 'list' or provide username and password.")

if __name__ == "__main__":
    main()