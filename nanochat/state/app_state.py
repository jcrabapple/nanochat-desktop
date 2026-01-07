import logging
import asyncio
from datetime import datetime
from nanochat.data import DatabaseManager, ConversationRepository, MessageRepository, ProjectRepository
from nanochat.api import NanoGPTClient
from nanochat.api.model_cache import ModelCache
from nanochat.config import config
from nanochat.state.conversation_mode import ConversationMode, get_mode_config

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

        # Model cache
        self.model_cache = ModelCache()

        # Current conversation
        self.current_conversation_id = None

        # Current conversation mode (default to STANDARD)
        self.current_conversation_mode = ConversationMode.STANDARD

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
                    'web_search_enabled': getattr(conv, 'web_search_enabled', False),
                    'project_id': getattr(conv, 'project_id', None)
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

    async def generate_conversation_title(self, conversation_id: int) -> str:
        """
        Generate a title for a conversation using the AI.

        Args:
            conversation_id: ID of the conversation to title

        Returns:
            Generated title string, or None if generation failed
        """
        if not self.api_client:
            logger.warning("Cannot generate title: API client not initialized")
            return None

        # Get conversation messages
        messages = self.get_conversation_messages(conversation_id)
        if len(messages) < 2:
            logger.info("Not enough messages to generate title")
            return None

        # Get first user message and first assistant response
        user_msg = None
        assistant_msg = None
        for msg in messages:
            if msg['role'] == 'user' and not user_msg:
                user_msg = msg['content'][:500]  # Limit length
            elif msg['role'] == 'assistant' and not assistant_msg:
                assistant_msg = msg['content'][:500]  # Limit length
            if user_msg and assistant_msg:
                break

        if not user_msg or not assistant_msg:
            return None

        # Create prompt for title generation
        title_prompt = f"""Based on this conversation, generate a very short title (3-6 words max). 
Only respond with the title itself, no quotes or explanation.

User: {user_msg}
Assistant: {assistant_msg}"""

        gen = None
        try:
            # Use API client to generate title (non-streaming for reliability)
            title = ""
            logger.info(f"Starting title generation for conversation {conversation_id}")
            gen = self.api_client.send_message(
                message=title_prompt,
                conversation_history=[],
                use_web_search=False,
                stream=False,  # Non-streaming for simpler, more reliable response
                temperature=0.7,
                max_tokens=150,  # Increased for models that use reasoning tokens
                model=config.title_model
            )
            chunk_count = 0
            async for chunk in gen:
                chunk_count += 1
                if chunk.content:
                    title += chunk.content
                if chunk.done:
                    break

            # Clean up the title
            title = title.strip().strip('"\'')
            if len(title) > 100:
                title = title[:100]

            # Save the title
            if title:
                self.rename_conversation(conversation_id, title)
                logger.info(f"Generated title for conversation {conversation_id}: {title}")
                return title
            else:
                logger.warning("Title generation returned empty title")

        except Exception as e:
            logger.error(f"Failed to generate title: {e}", exc_info=True)
            return None
        finally:
            # Ensure generator is properly closed
            if gen is not None:
                try:
                    await gen.aclose()
                except Exception as close_error:
                    logger.debug(f"Error closing generator: {close_error}")

        return None

    def set_web_search_enabled(self, conversation_id: int, enabled: bool) -> bool:
        """Set web search preference for a conversation"""
        with self.db.get_session() as session:
            conv_repo = ConversationRepository(session)
            conversation = conv_repo.update_web_search_enabled(conversation_id, enabled)
            return conversation is not None

    def set_conversation_mode(self, mode: ConversationMode):
        """
        Set current conversation mode.

        Args:
            mode: The conversation mode to switch to
        """
        self.current_conversation_mode = mode
        logger.info(f"Conversation mode set to {mode.value}")

    def get_conversation_mode(self) -> ConversationMode:
        """Get current conversation mode"""
        return self.current_conversation_mode

    def get_mode_config(self):
        """Get configuration for current mode"""
        return get_mode_config(self.current_conversation_mode)

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

    def get_cached_models(self):
        """
        Get cached models if available

        Returns:
            List of model IDs if cache is valid, None otherwise
        """
        return self.model_cache.get_cached_models()

    def cache_models(self, models: list):
        """
        Save models to cache

        Args:
            models: List of model IDs to cache
        """
        self.model_cache.save_models(models)

    async def fetch_models(self):
        """
        Fetch available models from API

        Returns:
            List of model IDs

        Raises:
            ValueError: If API client not initialized
            Exception: If API request fails
        """
        if not self.api_client:
            raise ValueError("API client not initialized")

        models = await self.api_client.fetch_models()

        # Cache the models
        self.model_cache.save_models(models)

        logger.info(f"Fetched and cached {len(models)} models")
        return models

    # ==================== Project Management ====================

    def create_project(self, name: str, color: str = '#4a9eff', description: str = None) -> dict:
        """
        Create a new project.

        Args:
            name: Project name (must be unique)
            color: Hex color code
            description: Optional description

        Returns:
            Dict with project data
        """
        with self.db.get_session() as session:
            proj_repo = ProjectRepository(session)
            project = proj_repo.create_project(
                name=name,
                color=color,
                description=description
            )
            logger.info(f"Created project {project.id}: {name}")
            return {
                'id': project.id,
                'name': project.name,
                'color': project.color,
                'description': project.description,
                'conversation_count': 0
            }

    def get_all_projects(self) -> list:
        """
        Get all projects.

        Returns:
            List of project dicts
        """
        with self.db.get_session() as session:
            proj_repo = ProjectRepository(session)
            projects = proj_repo.get_all_projects()

            return [
                {
                    'id': proj.id,
                    'name': proj.name,
                    'color': proj.color,
                    'description': proj.description,
                    'conversation_count': len(proj.conversations)
                }
                for proj in projects
            ]

    def update_project(self, project_id: int, name: str = None, color: str = None, description: str = None) -> bool:
        """
        Update a project.

        Args:
            project_id: Project ID
            name: New name (optional)
            color: New color (optional)
            description: New description (optional)

        Returns:
            True if updated, False if not found
        """
        with self.db.get_session() as session:
            proj_repo = ProjectRepository(session)
            project = proj_repo.update_project(
                project_id=project_id,
                name=name,
                color=color,
                description=description
            )
            return project is not None

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project (conversations are moved to 'No Project').

        Args:
            project_id: Project ID

        Returns:
            True if deleted, False if not found
        """
        with self.db.get_session() as session:
            proj_repo = ProjectRepository(session)
            return proj_repo.delete_project(project_id)

    def move_conversation_to_project(self, conversation_id: int, project_id: int = None) -> bool:
        """
        Move a conversation to a project.

        Args:
            conversation_id: Conversation ID
            project_id: Target project ID (None to move to 'No Project')

        Returns:
            True if moved, False if conversation not found
        """
        with self.db.get_session() as session:
            proj_repo = ProjectRepository(session)
            return proj_repo.assign_conversation_to_project(conversation_id, project_id)

    def get_conversations_for_project(self, project_id: int = None) -> list:
        """
        Get all conversations for a specific project.

        Args:
            project_id: Project ID (None for unorganized conversations)

        Returns:
            List of conversation dicts
        """
        with self.db.get_session() as session:
            proj_repo = ProjectRepository(session)
            conversations = proj_repo.get_conversations_by_project(project_id)

            return [
                {
                    'id': conv.id,
                    'title': conv.title,
                    'updated_at': conv.updated_at.isoformat(),
                    'message_count': len(conv.messages),
                    'web_search_enabled': getattr(conv, 'web_search_enabled', False),
                    'project_id': conv.project_id
                }
                for conv in conversations
            ]
