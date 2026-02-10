"""
Roadmap Agent - "Curriculum Designer Persona"
Generates personalized learning roadmaps for Student Mode
Uses LangChain LCEL with PydanticOutputParser for structured output
"""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.agents.core.llm import get_optimal_model
from app.agents.core.resilience import resilient_llm_call
from app.agents.prompts import get_agent_prompt
from app.core.logging import logger
from app.schemas.protocol import LearningRoadmap


async def run_roadmap_agent(
    requirements_spec: str,
    skill_level: str = "beginner",
    focus_areas: str = "",
) -> LearningRoadmap:
    """
    Roadmap Agent execution

    Generates a structured learning roadmap based on project requirements
    and the student's skill level.

    Args:
        requirements_spec: JSON string or text of the RequirementsDoc
        skill_level: One of 'beginner', 'intermediate', 'advanced'
        focus_areas: Comma-separated focus areas (optional)

    Returns:
        LearningRoadmap — Pydantic-enforced curriculum structure

    Security:
        - Output enforced via Pydantic schema (no hallucinated fields)
        - Input passed through LangChain prompt template
    """
    logger.info(
        f"Running Roadmap Agent (skill_level={skill_level}, "
        f"focus_areas={focus_areas or 'none'})..."
    )

    # Use pedagogy model (Claude) — best for educational content
    llm = get_optimal_model("pedagogy")
    parser = PydanticOutputParser(pydantic_object=LearningRoadmap)

    system_prompt = get_agent_prompt("roadmap")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "Project Requirements:\n{requirements_spec}\n\n"
                "Student Skill Level: {skill_level}\n"
                "Focus Areas: {focus_areas}\n\n"
                "Create a personalized learning roadmap that guides the student "
                "through building this project step by step.",
            ),
        ]
    )

    chain = prompt | llm | parser

    result = await resilient_llm_call(
        chain.ainvoke,
        {
            "requirements_spec": requirements_spec,
            "skill_level": skill_level,
            "focus_areas": focus_areas or "all project-relevant topics",
            "format_instructions": parser.get_format_instructions(),
        },
        agent_type="roadmap",
    )

    logger.info(
        f"Roadmap Agent completed: {len(result.modules)} modules, "
        f"{result.total_estimated_hours}h estimated"
    )
    return result
