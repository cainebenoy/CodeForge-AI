"""
Research Agent - "Product Manager Persona"
Generates requirements specification from user input
Uses LangChain LCEL with PydanticOutputParser for enforced structured output
"""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.agents.core.llm import get_optimal_model
from app.agents.prompts import get_agent_prompt
from app.core.logging import logger
from app.schemas.protocol import RequirementsDoc


async def run_research_agent(
    user_idea: str, target_audience: str = ""
) -> RequirementsDoc:
    """
    Research Agent execution

    Analyzes a user's app idea and generates a structured requirements document.

    Args:
        user_idea: The user's app idea description
        target_audience: Optional target audience description

    Returns:
        RequirementsDoc — Pydantic-enforced schema prevents LLM hallucination

    Security:
        - Input passed through LangChain prompt template (no injection)
        - Output enforced via Pydantic schema (no hallucinated fields)
    """
    logger.info(f"Running Research Agent for idea: {user_idea[:80]}...")

    llm = get_optimal_model("research")
    parser = PydanticOutputParser(pydantic_object=RequirementsDoc)

    # Use centralized system prompt + format instructions
    system_prompt = get_agent_prompt("research")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "App Idea: {user_idea}\nTarget Audience: {target_audience}\n\n"
                "Analyze this idea and generate a complete requirements specification.",
            ),
        ]
    )

    chain = prompt | llm | parser

    result = await chain.ainvoke(
        {
            "user_idea": user_idea,
            "target_audience": target_audience or "General users",
            "format_instructions": parser.get_format_instructions(),
        }
    )

    logger.info(f"Research Agent completed: {result.app_name}")
    return result
