from crewai import Agent
from tools.retrieval_tool import RetrievalTool
from config.settings import settings


def create_retriever_agent() -> Agent:
    """
    Create the Retriever Agent.

    This agent specializes in finding relevant information using hybrid search.
    """
    return Agent(
        role="RAG Retrieval Specialist",
        goal="Retrieve the most relevant document chunks for the user's query using hybrid search",
        backstory="""You are an expert at understanding user intent and finding relevant information
from large document collections. You excel at query expansion and semantic understanding.
You use both vector similarity and keyword matching to find the best results.""",
        tools=[RetrievalTool()],
        verbose=True,
        allow_delegation=False
    )
