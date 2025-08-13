"""
Database Migration Script
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.infrastructure.db.base import init_db, close_db


async def migrate_database():
    """Migrate database tables"""
    print("🔧 Starting database migration...")
    print(f"📊 Database URL: {settings.DATABASE_URL}")
    print(f"🔧 Environment: {settings.ENVIRONMENT}")
    
    try:
        # Initialize database (create tables)
        await init_db()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False
    
    finally:
        # Close database connections
        await close_db()
    
    return True


async def main():
    """Main migration function"""
    success = await migrate_database()
    if success:
        print("\n🎉 Database is ready for testing!")
    else:
        print("\n❌ Database migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
