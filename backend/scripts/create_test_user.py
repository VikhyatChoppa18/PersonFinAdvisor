"""
Script to create a test user for development.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.db import models
from app.core.security import get_password_hash

def create_test_user():
    """Create a default test user."""
    db = SessionLocal()
    try:
        # Check if test user already exists
        existing_user = db.query(models.User).filter(
            models.User.email == "test@example.com"
        ).first()
        
        if existing_user:
            print("Test user already exists!")
            print(f"Email: test@example.com")
            print(f"Password: testpass123")
            return
        
        # Create test user
        hashed_password = get_password_hash("testpass123")
        user = models.User(
            email="test@example.com",
            hashed_password=hashed_password,
            full_name="Test User",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("✅ Test user created successfully!")
        print("\nCredentials:")
        print("=" * 50)
        print("Email: test@example.com")
        print("Password: testpass123")
        print("=" * 50)
        print("\nYou can now login at: http://localhost:3001")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()

