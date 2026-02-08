import logging
from typing import List, Dict, Any
from config.settings import settings
from database.connection import SessionLocal
from database.repositories.conversation_repo import ConversationRepository
from database.repositories.message_repo import MessageRepository
import tiktoken


logger = logging.getLogger("backend.memory_service")


class MemoryService:
    """Service for managing conversation memory."""

    def __init__(self):
        """Initialize the memory service."""
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.max_messages = settings.max_memory_messages
        self.max_tokens = settings.max_memory_tokens
        logger.info("MemoryService initialized")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))

    async def get_conversation_history(
        self,
        session_id: str
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of message dictionaries
        """
        async with SessionLocal() as session:
            conv_repo = ConversationRepository(session)
            msg_repo = MessageRepository(session)

            # Get or create conversation
            conversation = await conv_repo.get_or_create(session_id)

            # Get recent messages
            messages = await msg_repo.get_by_conversation(
                conversation.id,
                limit=self.max_messages
            )

            # Convert to dict format and apply token limit
            history = []
            total_tokens = 0

            for msg in reversed(messages):
                msg_dict = {
                    "role": msg.role,
                    "content": msg.content
                }

                msg_tokens = self.count_tokens(msg.content)

                if total_tokens + msg_tokens > self.max_tokens:
                    break

                history.insert(0, msg_dict)
                total_tokens += msg_tokens

            logger.info(
                f"Retrieved {len(history)} messages "
                f"({total_tokens} tokens) for session {session_id}"
            )

            return history

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: List[Dict] = None
    ) -> None:
        """
        Add a message to conversation history.

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            citations: Optional citations list
        """
        async with SessionLocal() as session:
            conv_repo = ConversationRepository(session)
            msg_repo = MessageRepository(session)

            # Get or create conversation
            conversation = await conv_repo.get_or_create(session_id)

            # Add message
            await msg_repo.create(
                conversation_id=conversation.id,
                role=role,
                content=content,
                citations=citations or []
            )

            logger.info(f"Added {role} message to session {session_id}")

    async def clear_conversation(self, session_id: str) -> bool:
        """
        Clear conversation history.

        Args:
            session_id: Session identifier

        Returns:
            True if cleared, False if not found
        """
        async with SessionLocal() as session:
            conv_repo = ConversationRepository(session)
            result = await conv_repo.delete(session_id)

            if result:
                logger.info(f"Cleared conversation {session_id}")
            else:
                logger.warning(f"Conversation {session_id} not found")

            return result
