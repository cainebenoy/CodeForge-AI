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
from app.schemas.protocol import CodeGenerationResult, RefactorResult


async def run_code_agent(
    architecture: str, file_path: str = ""
) -> CodeGenerationResult:
    """
    Code Agent execution

    Uses Gemini 1.5 Pro for large context awareness (1M token window).
    Generates production-ready code files based on architecture spec.
    Enriches context with similar successful patterns from the RAG store.

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

    # RAG: search for similar successful code patterns
    rag_context = ""
    try:
        from app.agents.core.memory import search_similar_patterns

        patterns = await search_similar_patterns(
            project_type="code",
            query_text=architecture[:500],  # Use first 500 chars as query
            limit=3,
        )
        if patterns:
            rag_context = "\n\nSuccessful architectural patterns for reference:\n"
            for i, p in enumerate(patterns, 1):
                meta = p.get("metadata", {})
                rag_context += (
                    f"{i}. {meta.get('description', 'N/A')} "
                    f"(score: {p.get('success_score', 0):.1f})\n"
                )
            logger.info(f"RAG enriched code gen with {len(patterns)} patterns")
    except Exception as e:
        logger.warning(f"RAG pattern search failed (non-critical): {e}")

    llm = get_optimal_model("code")
    parser = PydanticOutputParser(pydantic_object=CodeGenerationResult)

    system_prompt = get_agent_prompt("code")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "Architecture:\n{architecture}\n\n"
                "{rag_context}"
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
            "rag_context": rag_context,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    logger.info(f"Code Agent completed: {len(result.files)} files generated")
    return result


async def run_refactor_agent(
    file_path: str,
    selected_code: str,
    instruction: str,
    full_file_content: str,
) -> RefactorResult:
    """
    Refactor Agent execution

    Refactors a selected code segment according to the user's instruction,
    preserving surrounding code structure.

    Args:
        file_path: Path of the file being refactored (for context)
        selected_code: The highlighted code segment to refactor
        instruction: What to do (e.g. "Make this more accessible")
        full_file_content: Complete file content for context

    Returns:
        RefactorResult — original code, refactored code, explanation, full file

    Security:
        - Output validated via Pydantic schema
        - File content size bounded by endpoint validation
    """
    logger.info(f"Running Refactor Agent for {file_path}: '{instruction[:60]}...'")

    llm = get_optimal_model("code")
    parser = PydanticOutputParser(pydantic_object=RefactorResult)

    system_prompt = get_agent_prompt("refactor")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "File: {file_path}\n\n"
                "Full file content:\n```\n{full_file_content}\n```\n\n"
                "Selected code to refactor:\n```\n{selected_code}\n```\n\n"
                "Instruction: {instruction}\n\n"
                "Refactor the selected code segment according to the instruction. "
                "Return the original code, refactored code, explanation, and the "
                "complete file content with the refactored segment applied.",
            ),
        ]
    )

    chain = prompt | llm | parser

    result = await chain.ainvoke(
        {
            "file_path": file_path,
            "full_file_content": full_file_content,
            "selected_code": selected_code,
            "instruction": instruction,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    logger.info(f"Refactor Agent completed for {file_path}")
    return result
