from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models import Conversation, Message
import uuid


class ConversationRepository:
    """Repository for conversation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_session_id(self, session_id: str) -> Optional[Conversation]:
        """
        Get conversation by session ID.

        Args:
            session_id: Session identifier

        Returns:
            Conversation object or None
        """
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def create(self, session_id: str, metadata: dict = None) -> Conversation:
        """
        Create a new conversation.

        Args:
            session_id: Session identifier
            metadata: Optional metadata dictionary

        Returns:
            Created Conversation object
        """
        conversation = Conversation(
            session_id=session_id,
            metadata=metadata or {}
        )
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def get_or_create(self, session_id: str) -> Conversation:
        """
        Get existing conversation or create new one.

        Args:
            session_id: Session identifier

        Returns:
            Conversation object
        """
        conversation = await self.get_by_session_id(session_id)
        if not conversation:
            conversation = await self.create(session_id)
        return conversation

    async def delete(self, session_id: str) -> bool:
        """
        Delete a conversation by session ID.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        conversation = await self.get_by_session_id(session_id)
        if conversation:
            await self.session.delete(conversation)
            await self.session.commit()
            return True
        return False

    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """
        List all conversations with pagination.

        Args:
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List of Conversation objects
        """
        result = await self.session.execute(
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
