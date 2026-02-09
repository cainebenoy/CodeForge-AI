"""
Code Agent - "Senior Developer Persona"
Generates production-ready code files
Uses LangChain LCEL with PydanticOutputParser for structured output
"""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.agents.core.llm import get_optimal_model
from app.agents.prompts import get_agent_prompt
from app.core.logging import logger
from app.schemas.protocol import CodeGenerationResult


async def run_code_agent(
    architecture: str, file_path: str = ""
) -> CodeGenerationResult:
    """
    Code Agent execution

    Uses Gemini 1.5 Pro for large context awareness (1M token window).
    Generates production-ready code files based on architecture spec.

    Args:
        architecture: JSON string or text of the WireframeSpec/architecture
        file_path: Optional specific file to generate (empty = generate all)

    Returns:
        CodeGenerationResult — Pydantic-enforced with file paths, content, dependencies

    Security:
        - NEVER hard-codes API keys (enforced in system prompt)
        - Output validated via Pydantic schema
    """
    logger.info(f"Running Code Agent (file_path={file_path or 'all'})...")

    llm = get_optimal_model("code")
    parser = PydanticOutputParser(pydantic_object=CodeGenerationResult)

    system_prompt = get_agent_prompt("code")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "Architecture:\n{architecture}\n\n"
                "File to generate: {file_path}\n\n"
                "Generate production-ready code. Include complete file content, "
                "list all npm dependencies needed, and provide a summary.",
            ),
        ]
    )

    chain = prompt | llm | parser

    result = await chain.ainvoke(
        {
            "architecture": architecture,
            "file_path": file_path or "all files needed for the application",
            "format_instructions": parser.get_format_instructions(),
        }
    )

    logger.info(f"Code Agent completed: {len(result.files)} files generated")
    return result
