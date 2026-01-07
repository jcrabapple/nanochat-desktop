"""
Migration v3: Add suggested_prompts table

This migration creates a table for storing suggested prompts that appear on the welcome screen.
"""

from sqlalchemy import text
from nanochat.data.database import DatabaseManager


def upgrade(database_manager: DatabaseManager):
    """Create suggested_prompts table"""
    with database_manager.get_session() as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS suggested_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text VARCHAR(500) NOT NULL,
                category VARCHAR(50) NOT NULL,
                display_order INTEGER DEFAULT 0 NOT NULL,
                is_active BOOLEAN DEFAULT 1 NOT NULL,
                usage_count INTEGER DEFAULT 0 NOT NULL,
                created_at DATETIME NOT NULL
            )
        """))
        session.commit()

        # Insert default suggested prompts
        default_prompts = [
            # General prompts
            ("How does AI work?", "general", 1),
            ("Are black holes real?", "general", 2),
            ("What is the meaning of life?", "general", 3),
            ("Explain quantum computing", "general", 4),

            # Create prompts
            ("Write a poem about spring", "create", 1),
            ("Create a marketing plan for a coffee shop", "create", 2),
            ("Draft an email to request a meeting", "create", 3),
            ("Write a short story about time travel", "create", 4),

            # Explore prompts
            ("What's the latest news in technology?", "explore", 1),
            ("Compare renewable energy sources", "explore", 2),
            ("What are the current trends in AI?", "explore", 3),
            ("Explain the history of the internet", "explore", 4),

            # Code prompts
            ("Write a Python function to sort a list", "code", 1),
            ("Create a React component for a button", "code", 2),
            ("Debug this SQL query", "code", 3),
            ("Explain Big O notation", "code", 4),

            # Learn prompts
            ("Teach me about machine learning", "learn", 1),
            ("How does blockchain technology work?", "learn", 2),
            ("Explain the basics of investing", "learn", 3),
            ("What is cognitive behavioral therapy?", "learn", 4),
        ]

        for text, category, display_order in default_prompts:
            session.execute(text("""
                INSERT INTO suggested_prompts (text, category, display_order, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """), (text, category, display_order))

        session.commit()
        print("Migration v3: Created suggested_prompts table with default prompts")


def downgrade(database_manager: DatabaseManager):
    """Remove suggested_prompts table"""
    with database_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS suggested_prompts"))
        session.commit()
        print("Migration v3 downgrade: Dropped suggested_prompts table")
