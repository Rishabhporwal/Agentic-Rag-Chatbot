from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.memory_service import MemoryService


router = APIRouter()
memory_service = MemoryService()


@router.get("/conversations/{session_id}")
async def get_conversation(session_id: str) -> Dict[str, Any]:
    """
    Get conversation history for a session.

    Args:
        session_id: Session identifier

    Returns:
        Conversation data with messages
    """
    try:
        messages = await memory_service.get_conversation_history(session_id)

        return {
            "session_id": session_id,
            "messages": messages,
            "message_count": len(messages)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{session_id}")
async def delete_conversation(session_id: str) -> Dict[str, str]:
    """
    Delete a conversation.

    Args:
        session_id: Session identifier

    Returns:
        Status message
    """
    try:
        result = await memory_service.clear_conversation(session_id)

        if result:
            return {"status": "deleted", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
