from crewai import Agent
from tools.reranking_tool import RerankingTool


def create_reranker_agent() -> Agent:
    """
    Create the Reranker Agent.

    This agent specializes in evaluating and reranking search results.
    """
    return Agent(
        role="Relevance Ranking Specialist",
        goal="Rerank retrieved chunks by relevance to the user query, removing redundant or low-quality results",
        backstory="""You are a precision-focused expert who evaluates document relevance through multiple lenses:
semantic similarity, query-document alignment, and information diversity. You remove redundant information
and ensure only the most relevant chunks are passed forward.""",
        tools=[RerankingTool()],
        verbose=True,
        allow_delegation=False
    )
