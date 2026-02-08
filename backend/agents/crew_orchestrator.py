"""
Crew Orchestrator

Coordinates the sequential execution of specialized agents for Agentic RAG.
"""

from crewai import Crew, Task, Process
from agents.retriever_agent import create_retriever_agent
from agents.reranker_agent import create_reranker_agent
from agents.synthesizer_agent import create_synthesizer_agent
from agents.guardrails_agent import create_guardrails_agent
import logging
import json


logger = logging.getLogger("backend.crew_orchestrator")


class AgenticRAGCrew:
    """Orchestrates the Agentic RAG crew."""

    def __init__(self):
        """Initialize the crew with all agents."""
        self.retriever = create_retriever_agent()
        self.reranker = create_reranker_agent()
        self.synthesizer = create_synthesizer_agent()
        self.guardrails = create_guardrails_agent()

        logger.info("AgenticRAGCrew initialized with 4 agents")

    def execute(
        self,
        query: str,
        session_id: str = None,
        top_k: int = 20,
        rerank_top_k: int = 5
    ) -> dict:
        """
        Execute the full agentic RAG pipeline.

        Args:
            query: User query
            session_id: Optional session ID for conversation memory
            top_k: Number of chunks to retrieve
            rerank_top_k: Number of chunks after reranking

        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"Executing crew for query: {query[:100]}...")

        try:
            # Task 1: Retrieval
            retrieval_task = Task(
                description=f"""Retrieve the most relevant document chunks for this query using hybrid search.
Query: {query}
Retrieve top {top_k} chunks.

Use the retrieval_tool to find relevant information.""",
                agent=self.retriever,
                expected_output="JSON with retrieved chunks and scores"
            )

            # Task 2: Reranking
            reranking_task = Task(
                description=f"""Rerank the retrieved chunks by relevance to the query.
Take the chunks from the previous task and rerank them.
Return the top {rerank_top_k} most relevant chunks.

Use the reranking_tool to evaluate relevance.""",
                agent=self.reranker,
                expected_output="JSON with reranked top chunks"
            )

            # Task 3: Synthesis
            synthesis_task = Task(
                description=f"""Generate a comprehensive answer to the user's query using the reranked chunks.

Query: {query}
Session ID: {session_id or 'none'}

Instructions:
1. If session_id is provided, use memory_tool to get conversation history
2. Use the top chunks from reranking to generate your answer
3. Include inline citations [1], [2], etc. for each claim
4. Use citation_tool to extract and format citations
5. Be comprehensive but concise
6. Never hallucinate - only use information from the provided chunks

Provide the final answer with citations.""",
                agent=self.synthesizer,
                expected_output="Generated answer with inline citations and citation metadata"
            )

            # Task 4: Guardrails
            guardrails_task = Task(
                description=f"""Review the generated response for quality and safety.

Check for:
1. Factual accuracy - are claims supported by the chunks?
2. Citation validity - are all citations properly referenced?
3. Hallucinations - is anything mentioned that wasn't in the context?
4. Harmful content - is the response safe and appropriate?
5. Completeness - does it answer the query?

If the response passes all checks, output it unchanged.
If there are issues, provide feedback and a corrected version.""",
                agent=self.guardrails,
                expected_output="Approved response or corrected version with explanation"
            )

            # Create crew with sequential process
            crew = Crew(
                agents=[self.retriever, self.reranker, self.synthesizer, self.guardrails],
                tasks=[retrieval_task, reranking_task, synthesis_task, guardrails_task],
                process=Process.sequential,
                verbose=True
            )

            # Execute crew
            result = crew.kickoff()

            logger.info("Crew execution completed successfully")

            # Parse result (result is the output from the last task)
            return {
                "success": True,
                "response": str(result),
                "metadata": {
                    "agents_executed": 4,
                    "tasks_completed": 4
                }
            }

        except Exception as e:
            logger.error(f"Crew execution failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error processing your request. Please try again."
            }
