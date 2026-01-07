from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Text,
    ForeignKey, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


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
    """Conversation model for storing chat sessions"""
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    model_used = Column(String(50), default="gpt-4")
    web_search_enabled = Column(Boolean, default=False, nullable=False)

    # Project foreign key (nullable - conversations can be unorganized)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)

    # Relationship to project
    project = relationship("Project", back_populates="conversations")

    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}')>"


class Message(Base):
    """Message model for storing individual messages"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Web search metadata (for Phase 2+)
    used_web_search = Column(Boolean, default=False)
    web_sources = Column(Text, nullable=True)  # JSON string of sources

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', content_length={len(self.content)})>"


class SuggestedPrompt(Base):
    """Suggested prompt model for welcome screen"""
    __tablename__ = 'suggested_prompts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)  # 'general', 'create', 'explore', 'code', 'learn'
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SuggestedPrompt(id={self.id}, text='{self.text[:30]}...', category='{self.category}')>"
