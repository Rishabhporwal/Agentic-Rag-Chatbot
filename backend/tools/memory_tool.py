from crewai_tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from services.memory_service import MemoryService
import asyncio
import json


class MemoryInput(BaseModel):
    """Input schema for memory tool."""
    session_id: str = Field(..., description="Session identifier")


class MemoryTool(BaseTool):
    name: str = "memory_tool"
    description: str = "Retrieves conversation history for context"
    args_schema: Type[BaseModel] = MemoryInput

    def _run(self, session_id: str) -> str:
        """
        Get conversation history.

        Args:
            session_id: Session identifier

        Returns:
            JSON string with conversation history
        """
        memory_service = MemoryService()
        history = asyncio.run(memory_service.get_conversation_history(session_id))

        output = {
            "success": True,
            "session_id": session_id,
            "message_count": len(history),
            "messages": history
        }

        return json.dumps(output, indent=2)
