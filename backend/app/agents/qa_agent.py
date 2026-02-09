"""
QA Agent - "Testing Specialist Persona"
Validates generated code for errors and best practices
Uses LangChain LCEL with PydanticOutputParser for structured review output
"""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.agents.core.llm import get_optimal_model
from app.agents.prompts import get_agent_prompt
from app.core.logging import logger
from app.schemas.protocol import QAResult


async def run_qa_agent(code: str, file_path: str) -> QAResult:
    """
    QA Agent execution

    Reviews code for quality, security, and best practices.

    Args:
        code: The code content to review
        file_path: Path of the file being reviewed

    Returns:
        QAResult — Pydantic-enforced with issues, severity, and score

    Security:
        - Checks for hard-coded secrets
        - Validates security patterns
    """
    logger.info(f"Running QA Agent for file: {file_path}")

    llm = get_optimal_model("qa")
    parser = PydanticOutputParser(pydantic_object=QAResult)

    system_prompt = get_agent_prompt("qa")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "File: {file_path}\n\nCode to review:\n```\n{code}\n```\n\n"
                "Review this code thoroughly and provide a structured report "
                "with issues, severity levels, and a quality score.",
            ),
        ]
    )

    chain = prompt | llm | parser

    result = await chain.ainvoke(
        {
            "code": code,
            "file_path": file_path,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    logger.info(
        f"QA Agent completed: passed={result.passed}, score={result.score}, issues={len(result.issues)}"
    )
    return result
