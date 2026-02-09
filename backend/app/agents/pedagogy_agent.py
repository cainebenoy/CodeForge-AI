"""
Pedagogy Agent - "Socratic Mentor Persona"
Guides students through learning without giving direct answers
Uses LangChain LCEL with PydanticOutputParser for structured guidance
"""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.agents.core.llm import get_optimal_model
from app.agents.prompts import get_agent_prompt
from app.core.logging import logger
from app.schemas.protocol import PedagogyResponse


async def run_pedagogy_agent(
    student_question: str, student_code: str = ""
) -> PedagogyResponse:
    """
    Pedagogy Agent execution

    Uses the Socratic method to guide students without giving direct answers.

    Args:
        student_question: The student's question
        student_code: Optional code the student is working on

    Returns:
        PedagogyResponse — Pydantic-enforced with guided steps, no direct answers

    Security:
        - Never provides ready-made code
        - Guides through questions and hints
    """
    logger.info(f"Running Pedagogy Agent for question: {student_question[:80]}...")

    llm = get_optimal_model("pedagogy")
    parser = PydanticOutputParser(pydantic_object=PedagogyResponse)

    system_prompt = get_agent_prompt("pedagogy")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "Student's question: {student_question}\n\n"
                "Their current code:\n```\n{student_code}\n```\n\n"
                "Guide them through learning using the Socratic method. "
                "Do NOT give direct code answers.",
            ),
        ]
    )

    chain = prompt | llm | parser

    result = await chain.ainvoke(
        {
            "student_question": student_question,
            "student_code": student_code or "(no code provided)",
            "format_instructions": parser.get_format_instructions(),
        }
    )

    logger.info(f"Pedagogy Agent completed: {len(result.steps)} learning steps")
    return result
