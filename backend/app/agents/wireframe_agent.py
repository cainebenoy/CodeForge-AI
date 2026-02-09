"""
Wireframe Agent - "System Architect Persona"
Generates application architecture and component tree
Uses LangChain LCEL with PydanticOutputParser for enforced structured output
"""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.agents.core.llm import get_optimal_model
from app.agents.prompts import get_agent_prompt
from app.core.logging import logger
from app.schemas.protocol import WireframeSpec


async def run_wireframe_agent(requirements: str) -> WireframeSpec:
    """
    Wireframe Agent execution

    Takes requirements from Research Agent and designs application architecture.

    Args:
        requirements: JSON string or text of the RequirementsDoc

    Returns:
        WireframeSpec — Pydantic-enforced architecture specification

    Security:
        - Output enforced via Pydantic schema
        - Theme colors validated as hex format
    """
    logger.info("Running Wireframe Agent...")

    llm = get_optimal_model("wireframe")
    parser = PydanticOutputParser(pydantic_object=WireframeSpec)

    system_prompt = get_agent_prompt("wireframe")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "Requirements:\n{requirements}\n\n"
                "Design the application architecture with site map, components, "
                "state management needs, and theme colors.",
            ),
        ]
    )

    chain = prompt | llm | parser

    result = await chain.ainvoke(
        {
            "requirements": requirements,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    logger.info(f"Wireframe Agent completed: {len(result.site_map)} routes defined")
    return result
