from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Message
import uuid


class MessageRepository:
    """Repository for message operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        citations: list = None,
        metadata: dict = None
    ) -> Message:
        """
        Create a new message.

        Args:
            conversation_id: UUID of the conversation
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            citations: Optional list of citations
            metadata: Optional metadata dictionary

        Returns:
            Created Message object
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations or [],
            metadata=metadata or {}
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_by_conversation(
        self,
        conversation_id: uuid.UUID,
        limit: int = 10
    ) -> List[Message]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: UUID of the conversation
            limit: Maximum number of messages to return

        Returns:
            List of Message objects
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        # Return in chronological order
        return list(reversed(messages))
