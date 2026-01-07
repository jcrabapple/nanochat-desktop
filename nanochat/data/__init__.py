"""
Data layer for NanoChat Desktop

Implements SQLite database with SQLAlchemy ORM for conversation and message persistence.
"""

import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Database version
DB_VERSION = 1


# ==================== Migration System ====================

class Migration:
    """Base migration class"""

    def __init__(self, version: int, description: str):
        self.version = version
        self.description = description

    def up(self, engine):
        """Apply migration"""
        raise NotImplementedError

    def down(self, engine):
        """Rollback migration"""
        raise NotImplementedError


class Migration_v1(Migration):
    """Initial schema migration"""

    def __init__(self):
        super().__init__(1, "Create conversations and messages tables")

    def up(self, engine):
        """Create initial schema"""
        # Create all tables
        Base.metadata.create_all(bind=engine)

    def down(self, engine):
        """Drop all tables"""
        Base.metadata.drop_all(bind=engine)


class Migration_v2(Migration):
    """Add projects table and project_id to conversations"""

    def __init__(self):
        super().__init__(2, "Add projects table for conversation organization")

    def up(self, engine):
        """Create projects table and add project_id to conversations"""
        from sqlalchemy import text

        with engine.connect() as conn:
            # Create projects table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    color VARCHAR(7) DEFAULT '#4a9eff',
                    description TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    order_index INTEGER NOT NULL DEFAULT 0
                )
            """))

            # Add project_id column to conversations if it doesn't exist
            # SQLite doesn't have IF NOT EXISTS for ADD COLUMN, so we check first
            result = conn.execute(text("PRAGMA table_info(conversations)"))
            columns = [row[1] for row in result]
            if 'project_id' not in columns:
                conn.execute(text("""
                    ALTER TABLE conversations ADD COLUMN project_id INTEGER REFERENCES projects(id)
                """))

            conn.commit()

    def down(self, engine):
        """Drop projects table"""
        from sqlalchemy import text

        with engine.connect() as conn:
            # Note: SQLite doesn't support DROP COLUMN, so we can't remove project_id
            conn.execute(text("DROP TABLE IF EXISTS projects"))
            conn.commit()


class MigrationManager:
    """Database migration manager"""

    def __init__(self, db_manager: 'DatabaseManager'):
        """
        Initialize migration manager

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.migrations = {
            1: Migration_v1(),
            2: Migration_v2()
        }

    def get_current_version(self) -> int:
        """Get current database version from metadata table"""
        from sqlalchemy import inspect, text

        inspector = inspect(self.db_manager.engine)
        if 'alembic_version' in inspector.get_table_names():
            # Using alembic-style version table
            with self.db_manager.get_session() as session:
                result = session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                row = result.fetchone()
                return row[0] if row else 0
        return 0

    def set_version(self, version: int):
        """Set database version in metadata table"""
        from sqlalchemy import text

        # Create version table if it doesn't exist
        with self.db_manager.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num INTEGER PRIMARY KEY
                )
            """))
            conn.execute(text("""
                INSERT OR REPLACE INTO alembic_version (version_num)
                VALUES (:version)
            """), {"version": version})
            conn.commit()

    def migrate(self, target_version: int = None):
        """
        Run migrations to bring database to target version

        Args:
            target_version: Target version (defaults to latest)
        """
        current_version = self.get_current_version()

        if target_version is None:
            target_version = max(self.migrations.keys())

        if current_version == target_version:
            logger.info(f"Database already at version {target_version}")
            return

        if current_version < target_version:
            # Upgrade
            for version in range(current_version + 1, target_version + 1):
                if version in self.migrations:
                    migration = self.migrations[version]
                    logger.info(f"Applying migration {version}: {migration.description}")
                    migration.up(self.db_manager.engine)
                    self.set_version(version)
                    logger.info(f"Migration {version} completed")
        else:
            # Downgrade
            for version in range(current_version, target_version, -1):
                if version in self.migrations:
                    migration = self.migrations[version]
                    logger.info(f"Rolling back migration {version}: {migration.description}")
                    migration.down(self.db_manager.engine)
                    self.set_version(version - 1)
                    logger.info(f"Rollback {version} completed")

        logger.info(f"Database migrated to version {target_version}")


# ==================== ORM Models ====================

class Project(Base):
    """Project model for organizing conversations into folders"""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), default='#4a9eff')  # Hex color
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)

    # Relationship to conversations
    conversations = relationship("Conversation", back_populates="project")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class Conversation(Base):
    """Conversation model"""
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    web_search_enabled = Column(Boolean, default=False, nullable=False)

    # Project foreign key (nullable - conversations can be unorganized)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)

    # Relationship to project
    project = relationship("Project", back_populates="conversations")

    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", lazy='select')

    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', messages={len(self.messages)})>"


class Message(Base):
    """Message model"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    used_web_search = Column(Boolean, default=False, nullable=False)
    web_sources = Column(Text, nullable=True)  # JSON string of web sources

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role='{self.role}', content='{content_preview}')>"


# ==================== Database Manager ====================

class DatabaseManager:
    """Database connection and session manager"""

    def __init__(self, db_path: str):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path).expanduser()

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create database URL
        self.db_url = f"sqlite:///{self.db_path}"

        # Create engine
        self.engine = create_engine(
            self.db_url,
            echo=False,  # Set to True for SQL query logging
            connect_args={"check_same_thread": False}  # Needed for SQLite
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info(f"Database manager initialized: {self.db_path}")

    def init_db(self):
        """Initialize database schema with migrations"""
        try:
            # Run migrations
            migration_manager = MigrationManager(self)
            migration_manager.migrate()
            logger.info("Database initialization complete")
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @contextmanager
    def get_session(self):
        """
        Get a database session context manager

        Usage:
            with db.get_session() as session:
                # use session here
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def backup(self, backup_path: Optional[str] = None):
        """
        Create a backup of the database

        Args:
            backup_path: Optional path for backup file. Defaults to timestamped backup
        """
        import shutil
        from datetime import datetime

        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"conversations_backup_{timestamp}.db"

        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backup created: {backup_path}")
        return backup_path


# ==================== Repositories ====================

class ConversationRepository:
    """Repository for conversation CRUD operations"""

    def __init__(self, session: Session):
        """
        Initialize repository with a session

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create_conversation(self, title: str = "New Chat", web_search_enabled: bool = False) -> Conversation:
        """
        Create a new conversation

        Args:
            title: Conversation title
            web_search_enabled: Whether web search is enabled by default

        Returns:
            Created Conversation object
        """
        conversation = Conversation(
            title=title,
            web_search_enabled=web_search_enabled
        )
        self.session.add(conversation)
        self.session.flush()  # Get the ID without committing
        logger.info(f"Created conversation {conversation.id}: '{title}'")
        return conversation

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """
        Get a conversation by ID

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation object or None if not found
        """
        return self.session.query(Conversation).filter_by(id=conversation_id).first()

    def get_all_conversations(self) -> List[Conversation]:
        """
        Get all conversations ordered by updated_at descending

        Returns:
            List of Conversation objects
        """
        return self.session.query(Conversation)\
            .order_by(Conversation.updated_at.desc())\
            .all()

    def update_conversation_title(self, conversation_id: int, new_title: str) -> Optional[Conversation]:
        """
        Update conversation title

        Args:
            conversation_id: Conversation ID
            new_title: New title

        Returns:
            Updated Conversation object or None if not found
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.title = new_title
            conversation.updated_at = datetime.utcnow()
            self.session.flush()
            logger.info(f"Updated conversation {conversation_id} title: '{new_title}'")
        return conversation

    def update_web_search_enabled(self, conversation_id: int, enabled: bool) -> Optional[Conversation]:
        """
        Update web search preference for a conversation

        Args:
            conversation_id: Conversation ID
            enabled: Whether web search is enabled

        Returns:
            Updated Conversation object or None if not found
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.web_search_enabled = enabled
            conversation.updated_at = datetime.utcnow()
            self.session.flush()
            logger.info(f"Updated conversation {conversation_id} web_search: {enabled}")
        return conversation

    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Delete a conversation and all its messages

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            self.session.delete(conversation)
            self.session.flush()
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False

    def get_conversations_by_date_range(self, days: int = 7) -> List[Conversation]:
        """
        Get conversations updated within the last N days

        Args:
            days: Number of days to look back

        Returns:
            List of Conversation objects
        """
        cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
        return self.session.query(Conversation)\
            .filter(Conversation.updated_at >= cutoff_date)\
            .order_by(Conversation.updated_at.desc())\
            .all()


class MessageRepository:
    """Repository for message CRUD operations"""

    def __init__(self, session: Session):
        """
        Initialize repository with a session

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        used_web_search: bool = False,
        web_sources: Optional[str] = None
    ) -> Message:
        """
        Create a new message

        Args:
            conversation_id: ID of the conversation
            role: Message role ('user' or 'assistant')
            content: Message content
            used_web_search: Whether web search was used
            web_sources: JSON string of web sources

        Returns:
            Created Message object
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            used_web_search=used_web_search,
            web_sources=web_sources
        )
        self.session.add(message)

        # Update conversation's updated_at timestamp
        conversation = self.session.query(Conversation).get(conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()

        self.session.flush()
        logger.debug(f"Created message in conversation {conversation_id}: {role}")
        return message

    def get_message(self, message_id: int) -> Optional[Message]:
        """
        Get a message by ID

        Args:
            message_id: Message ID

        Returns:
            Message object or None if not found
        """
        return self.session.query(Message).filter_by(id=message_id).first()

    def get_messages(self, conversation_id: int) -> List[Message]:
        """
        Get all messages for a conversation ordered by created_at

        Args:
            conversation_id: Conversation ID

        Returns:
            List of Message objects
        """
        return self.session.query(Message)\
            .filter_by(conversation_id=conversation_id)\
            .order_by(Message.created_at.asc())\
            .all()

    def delete_messages(self, conversation_id: int) -> int:
        """
        Delete all messages for a conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            Number of messages deleted
        """
        count = self.session.query(Message)\
            .filter_by(conversation_id=conversation_id)\
            .delete()
        self.session.flush()
        logger.info(f"Deleted {count} messages from conversation {conversation_id}")
        return count

    def delete_message(self, message_id: int) -> bool:
        """
        Delete a specific message

        Args:
            message_id: Message ID

        Returns:
            True if deleted, False if not found
        """
        message = self.get_message(message_id)
        if message:
            self.session.delete(message)
            self.session.flush()
            logger.info(f"Deleted message {message_id}")
            return True
        return False

    def get_conversation_message_count(self, conversation_id: int) -> int:
        """
        Get the number of messages in a conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            Number of messages
        """
        return self.session.query(Message)\
            .filter_by(conversation_id=conversation_id)\
            .count()


class ProjectRepository:
    """Repository for project CRUD operations"""

    def __init__(self, session: Session):
        """
        Initialize repository with a session

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create_project(
        self,
        name: str,
        color: str = '#4a9eff',
        description: str = None
    ) -> Project:
        """
        Create a new project

        Args:
            name: Project name (must be unique)
            color: Hex color code for the project
            description: Optional project description

        Returns:
            Created Project object
        """
        # Get the next order index
        max_order = self.session.query(Project).count()

        project = Project(
            name=name,
            color=color,
            description=description,
            order_index=max_order
        )
        self.session.add(project)
        self.session.flush()
        logger.info(f"Created project: {project.id} - {project.name}")
        return project

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        return self.session.query(Project).filter_by(id=project_id).first()

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get project by name"""
        return self.session.query(Project).filter_by(name=name).first()

    def get_all_projects(self) -> List[Project]:
        """Get all projects ordered by order_index"""
        return self.session.query(Project).order_by(Project.order_index).all()

    def update_project(
        self,
        project_id: int,
        name: str = None,
        color: str = None,
        description: str = None
    ) -> Optional[Project]:
        """
        Update project attributes

        Args:
            project_id: Project ID
            name: New name (optional)
            color: New color (optional)
            description: New description (optional)

        Returns:
            Updated Project object or None if not found
        """
        project = self.get_project(project_id)
        if project:
            if name is not None:
                project.name = name
            if color is not None:
                project.color = color
            if description is not None:
                project.description = description
            project.updated_at = datetime.utcnow()
            self.session.flush()
            logger.info(f"Updated project {project_id}")
        return project

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project (conversations are moved to 'No Project')

        Args:
            project_id: Project ID

        Returns:
            True if deleted, False if not found
        """
        project = self.get_project(project_id)
        if project:
            # Unassign conversations from this project
            for conversation in project.conversations:
                conversation.project_id = None
            self.session.delete(project)
            self.session.flush()
            logger.info(f"Deleted project {project_id}")
            return True
        return False

    def assign_conversation_to_project(
        self,
        conversation_id: int,
        project_id: int = None
    ) -> bool:
        """
        Assign a conversation to a project (or None to unassign)

        Args:
            conversation_id: Conversation ID
            project_id: Project ID (None to unassign)

        Returns:
            True if successful, False if conversation not found
        """
        conversation = self.session.query(Conversation).filter_by(
            id=conversation_id
        ).first()
        if conversation:
            conversation.project_id = project_id
            conversation.updated_at = datetime.utcnow()
            self.session.flush()
            logger.info(f"Assigned conversation {conversation_id} to project {project_id}")
            return True
        return False

    def get_conversations_by_project(
        self,
        project_id: int = None,
        limit: int = 100
    ) -> List[Conversation]:
        """
        Get conversations for a specific project (None for unorganized)

        Args:
            project_id: Project ID (None for unorganized conversations)
            limit: Maximum number of conversations to return

        Returns:
            List of Conversation objects
        """
        return self.session.query(Conversation)\
            .filter_by(project_id=project_id)\
            .order_by(Conversation.updated_at.desc())\
            .limit(limit)\
            .all()
