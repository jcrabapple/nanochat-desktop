import logging
import asyncio
from datetime import datetime
from nanochat.data import DatabaseManager, ConversationRepository, MessageRepository
from nanochat.api import NanoGPTClient
from nanochat.config import config

logger = logging.getLogger(__name__)


class ApplicationState:
    """
    Main application controller
    Manages database, API client, and UI updates
    """

    def __init__(self):
        """Initialize application state"""
        # Database
        self.db = DatabaseManager(config.db_path)
        self.db.init_db()

        # API client (will be initialized when API key is available)
        self.api_client: NanoGPTClient = None

        # Current conversation
        self.current_conversation_id = None

        logger.info("Application state initialized")

    def init_api_client(self, api_key: str = None, base_url: str = None, model: str = None):
        """Initialize API client with configuration"""
        if not api_key:
            api_key = config.api_key
        if not base_url:
            base_url = config.api_base_url
        if not model:
            model = config.model

        self.api_client = NanoGPTClient(
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        logger.info("API client initialized")

    def create_conversation(self) -> int:
        """Create a new conversation"""
        with self.db.get_session() as session:
            conv_repo = ConversationRepository(session)
            conv = conv_repo.create_conversation()
            self.current_conversation_id = conv.id
            logger.info(f"Created conversation {conv.id}")
            return conv.id

    def load_conversation(self, conversation_id: int):
        """Load conversation and set as active"""
        self.current_conversation_id = conversation_id
        logger.info(f"Loaded conversation {conversation_id}")

    def get_conversation_messages(self, conversation_id: int) -> list:
        """Get all messages for a conversation"""
        import json

        with self.db.get_session() as session:
            msg_repo = MessageRepository(session)
            messages = msg_repo.get_messages(conversation_id)

            # Convert to dicts
            return [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat(),
                    'used_web_search': msg.used_web_search,
                    'web_sources': json.loads(msg.web_sources) if msg.web_sources else None
                }
                for msg in messages
            ]

    def get_all_conversations(self) -> list:
        """Get all conversations"""
        with self.db.get_session() as session:
            conv_repo = ConversationRepository(session)
            conversations = conv_repo.get_all_conversations()

            # Convert to dicts
            return [
                {
                    'id': conv.id,
                    'title': conv.title,
                    'updated_at': conv.updated_at.isoformat(),
                    'message_count': len(conv.messages),
                    'web_search_enabled': getattr(conv, 'web_search_enabled', False)
                }
                for conv in conversations
            ]

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation"""
        with self.db.get_session() as session:
            conv_repo = ConversationRepository(session)
            success = conv_repo.delete_conversation(conversation_id)

            # Clear current conversation if it was deleted
            if success and self.current_conversation_id == conversation_id:
                self.current_conversation_id = None

            return success

    def rename_conversation(self, conversation_id: int, new_title: str) -> bool:
        """Rename a conversation"""
        with self.db.get_session() as session:
            conv_repo = ConversationRepository(session)
            conversation = conv_repo.update_conversation_title(conversation_id, new_title)
            return conversation is not None

    def set_web_search_enabled(self, conversation_id: int, enabled: bool) -> bool:
        """Set web search preference for a conversation"""
        with self.db.get_session() as session:
            conv_repo = ConversationRepository(session)
            conversation = conv_repo.update_web_search_enabled(conversation_id, enabled)
            return conversation is not None

    def get_web_search_enabled(self, conversation_id: int) -> bool:
        """Get web search preference for a conversation"""
        with self.db.get_session() as session:
            conv_repo = ConversationRepository(session)
            conversation = conv_repo.get_conversation(conversation_id)
            if conversation:
                return getattr(conversation, 'web_search_enabled', False)
        return False

    async def send_message(self, message: str, use_web_search: bool = False):
        """
        Send message and get response

        Args:
            message: User message
            use_web_search: Whether to use web search

        Yields:
            Tuples of (role, content, web_sources) as they arrive
        """
        import json

        if not self.api_client:
            raise ValueError("API client not initialized")

        # Create conversation if needed
        if self.current_conversation_id is None:
            self.create_conversation()

        # Save user message
        with self.db.get_session() as session:
            msg_repo = MessageRepository(session)
            msg_repo.create_message(
                self.current_conversation_id,
                'user',
                message
            )

        # Yield user message
        yield ('user', message, None)

        # Get conversation history
        history = self.get_conversation_messages(self.current_conversation_id)

        # Send to API and stream response
        response_content = ""
        web_sources = None
        used_web_search = False

        # Create generator and ensure it's properly closed
        gen = self.api_client.send_message(
            message=message,
            conversation_history=history[:-1],  # Exclude the message we just added
            use_web_search=use_web_search,
            stream=True
        )

        try:
            async for chunk in gen:
                if chunk.content:
                    response_content += chunk.content
                    yield ('assistant', chunk.content, None)

                # Capture web_sources when available
                if chunk.web_sources:
                    web_sources = chunk.web_sources
                    used_web_search = True

                if chunk.done:
                    # Save assistant message WITH web_sources
                    with self.db.get_session() as session:
                        msg_repo = MessageRepository(session)
                        msg_repo.create_message(
                            self.current_conversation_id,
                            'assistant',
                            response_content,
                            used_web_search=used_web_search,
                            web_sources=json.dumps(web_sources) if web_sources else None
                        )

                    # Final yield with sources
                    yield ('assistant', None, web_sources)
                    break
        finally:
            # Ensure generator is closed to clean up resources
            await gen.aclose()
