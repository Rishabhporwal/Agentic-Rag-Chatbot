from fastapi import APIRouter, HTTPException
import time
import uuid
from models.requests import ChatCompletionRequest
from models.responses import (
    ChatCompletionResponse,
    Choice,
    ChatMessage,
    Usage,
    Citation,
    ResponseMetadata
)
from services.retrieval_service import RetrievalService
from services.llm_service import LLMService
from services.memory_service import MemoryService
from config.settings import settings
import logging


router = APIRouter()
logger = logging.getLogger("backend.chat")


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completion endpoint.

    This endpoint orchestrates the full RAG pipeline:
    1. Retrieve relevant chunks
    2. Rerank results
    3. Generate response with citations
    4. Apply guardrails

    Args:
        request: Chat completion request

    Returns:
        Chat completion response with citations
    """
    start_time = time.time()
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    try:
        # Initialize services
        retrieval_service = RetrievalService()
        llm_service = LLMService(
            base_url=settings.ollama_base_url,
            model=settings.llm_model
        )
        memory_service = MemoryService()

        # Get last user message
        user_message = next(
            (msg for msg in reversed(request.messages) if msg.role == "user"),
            None
        )

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        query = user_message.content

        # Get conversation history if session_id provided
        conversation_history = []
        if request.session_id:
            conversation_history = await memory_service.get_conversation_history(
                request.session_id
            )

        # Step 1: Retrieve relevant chunks
        logger.info(f"Retrieving chunks for query: {query[:100]}...")
        retrieval_start = time.time()

        retrieval_result = await retrieval_service.retrieve(
            query=query,
            top_k=request.retrieval_params.top_k or settings.retrieval_top_k,
            filters=request.retrieval_params.filters
        )

        retrieval_time = (time.time() - retrieval_start) * 1000
        chunks = retrieval_result["chunks"]

        if not chunks:
            # No relevant chunks found, generate response without RAG
            logger.warning("No relevant chunks found")
            response_text = "I couldn't find any relevant information in the knowledge base to answer your question."
            citations = []
        else:
            # Step 2: Simple reranking (take top-k by score)
            rerank_start = time.time()
            rerank_top_k = request.retrieval_params.rerank_top_k or settings.rerank_top_k
            reranked_chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)[:rerank_top_k]
            reranking_time = (time.time() - rerank_start) * 1000

            # Step 3: Generate response
            logger.info("Generating response...")
            generation_start = time.time()

            # Build context from chunks
            context = "\n\n".join([
                f"[{i+1}] {chunk['content']}"
                for i, chunk in enumerate(reranked_chunks[:settings.final_top_k])
            ])

            # Build prompt
            system_prompt = """You are a helpful assistant that answers questions based on the provided context.
Always cite your sources using the citation numbers [1], [2], etc. provided in the context.
If the context doesn't contain enough information to answer the question, say so."""

            # Combine conversation history and current query
            messages = conversation_history.copy()
            messages.append({
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}\n\nProvide an answer with citations."
            })

            # Generate response
            response_text = llm_service.chat(
                messages=[{"role": "system", "content": system_prompt}] + messages,
                temperature=request.temperature or settings.default_temperature,
                max_tokens=request.max_tokens or settings.default_max_tokens
            )

            generation_time = (time.time() - generation_start) * 1000

            # Extract citations from response
            citations = []
            for i, chunk in enumerate(reranked_chunks[:settings.final_top_k]):
                citation_num = i + 1
                if f"[{citation_num}]" in response_text:
                    citations.append(Citation(
                        id=citation_num,
                        chunk_id=chunk["id"],
                        document_id=chunk["document_id"],
                        document_name=chunk["metadata"].get("document_filename", "Unknown"),
                        page_number=chunk["metadata"].get("page_number"),
                        content=chunk["content"][:200] + "...",
                        relevance_score=chunk["score"]
                    ))

        # Save to conversation history
        if request.session_id:
            await memory_service.add_message(
                session_id=request.session_id,
                role="user",
                content=query
            )
            await memory_service.add_message(
                session_id=request.session_id,
                role="assistant",
                content=response_text,
                citations=[c.dict() for c in citations]
            )

        # Calculate token usage (approximate)
        prompt_tokens = sum(len(msg.content.split()) for msg in request.messages) * 2
        completion_tokens = len(response_text.split()) * 2

        # Build response
        total_time = (time.time() - start_time) * 1000

        return ChatCompletionResponse(
            id=completion_id,
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=response_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            ),
            citations=citations,
            metadata=ResponseMetadata(
                retrieval_time_ms=retrieval_time if chunks else 0,
                reranking_time_ms=reranking_time if chunks else 0,
                generation_time_ms=generation_time if chunks else total_time - retrieval_time,
                total_time_ms=total_time,
                chunks_retrieved=len(chunks),
                chunks_reranked=len(reranked_chunks) if chunks else 0,
                chunks_used=len(citations)
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
