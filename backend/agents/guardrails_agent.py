from crewai import Agent


def create_guardrails_agent() -> Agent:
    """
    Create the Guardrails Agent.

    This agent specializes in quality assurance and safety checks.
    """
    return Agent(
        role="Quality Assurance and Safety Specialist",
        goal="Ensure responses are safe, accurate, and appropriate before delivery to the user",
        backstory="""You are a vigilant guardian who checks responses for hallucinations, harmful content,
and factual accuracy. You verify that all citations are valid and that claims are supported by the provided context.
You have the authority to reject responses that don't meet quality standards.""",
        tools=[],
        verbose=True,
        allow_delegation=False
    )
