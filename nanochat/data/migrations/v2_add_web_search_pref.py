"""
Migration v2: Add web_search_enabled column to conversations table

This migration adds a column to store web search preference per conversation.
"""

from sqlalchemy import Boolean, text
from nanochat.data.database import DatabaseManager


def upgrade(database_manager: DatabaseManager):
    """Add web_search_enabled column to conversations table"""
    with database_manager.get_session() as session:
        # Add the column using raw SQL
        session.execute(text("ALTER TABLE conversations ADD COLUMN web_search_enabled BOOLEAN DEFAULT 0 NOT NULL"))
        session.commit()
        print("Migration v2: Added web_search_enabled column to conversations table")


def downgrade(database_manager: DatabaseManager):
    """Remove web_search_enabled column from conversations table"""
    with database_manager.get_session() as session:
        # SQLite doesn't support DROP COLUMN directly, need to recreate table
        session.execute(text("""
            CREATE TABLE conversations_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255) NOT NULL DEFAULT 'New Chat',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                model_used VARCHAR(50) DEFAULT 'gpt-4'
            )
        """))
        session.execute(text("""
            INSERT INTO conversations_new (id, title, created_at, updated_at, model_used)
            SELECT id, title, created_at, updated_at, model_used FROM conversations
        """))
        session.execute(text("DROP TABLE conversations"))
        session.execute(text("ALTER TABLE conversations_new RENAME TO conversations"))
        session.commit()
        print("Migration v2 downgrade: Removed web_search_enabled column")
