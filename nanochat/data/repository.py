import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from nanochat.data.models import Conversation, Message, Project

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation CRUD operations"""

    def __init__(self, session: Session):
        self.session = session

    def create_conversation(
        self,
        title: str = "New Chat",
        model: str = "gpt-4"
    ) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            title=title,
            model_used=model,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(conversation)
        self.session.flush()  # Get ID without committing
        logger.info(f"Created conversation: {conversation.id}")
        return conversation

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.session.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    def get_all_conversations(self, limit: int = 100) -> List[Conversation]:
        """Get all conversations, ordered by updated_at desc"""
        return self.session.query(Conversation).order_by(
            desc(Conversation.updated_at)
        ).limit(limit).all()

    def update_conversation_title(
        self,
        conversation_id: int,
        title: str
    ) -> Optional[Conversation]:
        """Update conversation title"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            self.session.flush()
            logger.info(f"Updated conversation {conversation_id} title")
        return conversation

    def update_web_search_enabled(
        self,
        conversation_id: int,
        enabled: bool
    ) -> Optional[Conversation]:
        """Update web search preference for a conversation"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.web_search_enabled = enabled
            conversation.updated_at = datetime.utcnow()
            self.session.flush()
            logger.info(f"Updated conversation {conversation_id} web_search_enabled to {enabled}")
        return conversation

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and all its messages"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            self.session.delete(conversation)
            self.session.flush()
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False


class MessageRepository:
    """Repository for message CRUD operations"""

    def __init__(self, session: Session):
        self.session = session

    def create_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        used_web_search: bool = False,
        web_sources: str = None
    ) -> Message:
        """Create a new message"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.utcnow(),
            used_web_search=used_web_search,
            web_sources=web_sources
        )
        self.session.add(message)
        self.session.flush()

        # Update conversation's updated_at timestamp
        conversation = self.session.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()

        logger.info(f"Created message in conversation {conversation_id}")
        return message

    def get_messages(
        self,
        conversation_id: int,
        limit: int = 100
    ) -> List[Message]:
        """Get all messages for a conversation"""
        return self.session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).limit(limit).all()

    def delete_message(self, message_id: int) -> bool:
        """Delete a message"""
        message = self.session.query(Message).filter(
            Message.id == message_id
        ).first()
        if message:
            self.session.delete(message)
            self.session.flush()
            return True
        return False


class ProjectRepository:
    """Repository for project CRUD operations"""

    def __init__(self, session: Session):
        self.session = session

    def create_project(
        self,
        name: str,
        color: str = '#4a9eff',
        description: str = None
    ) -> Project:
        """Create a new project"""
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
        return self.session.query(Project).filter(
            Project.id == project_id
        ).first()

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get project by name"""
        return self.session.query(Project).filter(
            Project.name == name
        ).first()

    def get_all_projects(self) -> List[Project]:
        """Get all projects ordered by order_index"""
        return self.session.query(Project).order_by(
            Project.order_index
        ).all()

    def update_project(
        self,
        project_id: int,
        name: str = None,
        color: str = None,
        description: str = None
    ) -> Optional[Project]:
        """Update project attributes"""
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
        """Delete a project (conversations are moved to 'No Project')"""
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
        """Assign a conversation to a project (or None to unassign)"""
        conversation = self.session.query(Conversation).filter(
            Conversation.id == conversation_id
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
        """Get conversations for a specific project (None for unorganized)"""
        query = self.session.query(Conversation).filter(
            Conversation.project_id == project_id
        ).order_by(desc(Conversation.updated_at))
        return query.limit(limit).all()

    def reorder_project(self, project_id: int, new_index: int) -> bool:
        """Change the order of a project"""
        projects = self.get_all_projects()
        project_to_move = None

        for p in projects:
            if p.id == project_id:
                project_to_move = p
                break

        if not project_to_move:
            return False

        # Remove from current position and reorder
        current_index = project_to_move.order_index
        if current_index == new_index:
            return True

        # Shift other projects
        for p in projects:
            if current_index < new_index:
                # Moving down: shift items up
                if current_index < p.order_index <= new_index:
                    p.order_index -= 1
            else:
                # Moving up: shift items down
                if new_index <= p.order_index < current_index:
                    p.order_index += 1

        project_to_move.order_index = new_index
        self.session.flush()
        logger.info(f"Reordered project {project_id} to index {new_index}")
        return True
