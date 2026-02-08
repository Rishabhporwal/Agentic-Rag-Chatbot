from crewai import Agent
from tools.memory_tool import MemoryTool
from tools.citation_tool import CitationTool


def create_synthesizer_agent() -> Agent:
    """
    Create the Synthesizer Agent.

    This agent specializes in generating comprehensive answers with citations.
    """
    return Agent(
        role="Answer Synthesis Expert",
        goal="Generate accurate, comprehensive answers by synthesizing information from provided contexts while maintaining factual grounding",
        backstory="""You are a skilled writer who can weave together information from multiple sources
into coherent, well-cited responses. You ALWAYS ground your answers in the provided context and NEVER hallucinate.
You use inline citations [1], [2], etc. to reference sources. If the context doesn't contain enough information,
you clearly state what is missing.""",
        tools=[MemoryTool(), CitationTool()],
        verbose=True,
        allow_delegation=False
    )
