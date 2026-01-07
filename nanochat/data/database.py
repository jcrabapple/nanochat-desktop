import os
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from nanochat.data.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and initialization"""

    def __init__(self, db_path: str = None):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file. If None, uses default location
        """
        if db_path is None:
            # Default: ~/.local/share/nanochat/conversations.db
            data_dir = Path.home() / ".local" / "share" / "nanochat"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "conversations.db")

        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()

    def _initialize_engine(self):
        """Create SQLAlchemy engine with SQLite"""
        # Ensure parent directory exists
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # SQLite connection URL
        database_url = f"sqlite:///{self.db_path}"

        # Create engine with connection pooling for SQLite
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # SQLite works best with StaticPool
            echo=False  # Set to True for SQL query logging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info(f"Database engine initialized: {self.db_path}")

    def init_db(self):
        """Initialize database schema"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database schema created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def drop_all(self):
        """Drop all tables (useful for testing)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")

    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions

        Usage:
            with db_manager.get_session() as session:
                # do work
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session_sync(self) -> Session:
        """Get a session for manual management (use with caution)"""
        return self.SessionLocal()
