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
from app.schemas.protocol import ClarificationResponse, RequirementsDoc


async def run_research_agent(
    user_idea: str, target_audience: str = ""
) -> RequirementsDoc:
    """
    Research Agent execution

    Analyzes a user's app idea and generates a structured requirements document.
    Enriches the prompt with similar successful project patterns from the RAG store.

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

    # RAG: search for similar patterns to enrich context
    rag_context = ""
    try:
        from app.agents.core.memory import search_similar_patterns

        patterns = await search_similar_patterns(
            project_type="research",
            query_text=user_idea,
            limit=3,
        )
        if patterns:
            rag_context = "\n\nSimilar successful project patterns for reference:\n"
            for i, p in enumerate(patterns, 1):
                meta = p.get("metadata", {})
                rag_context += f"{i}. {meta.get('description', 'N/A')} (score: {p.get('success_score', 0):.1f})\n"
            logger.info(f"RAG enriched research with {len(patterns)} patterns")
    except Exception as e:
        # RAG is non-critical — log and continue
        logger.warning(f"RAG pattern search failed (non-critical): {e}")

    llm = get_optimal_model("research")
    parser = PydanticOutputParser(pydantic_object=RequirementsDoc)

    # Use centralized system prompt + format instructions
    system_prompt = get_agent_prompt("research")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "App Idea: {user_idea}\nTarget Audience: {target_audience}\n"
                "{rag_context}\n\n"
                "Analyze this idea and generate a complete requirements specification.",
            ),
        ]
    )

    chain = prompt | llm | parser

    result = await chain.ainvoke(
        {
            "user_idea": user_idea,
            "target_audience": target_audience or "General users",
            "rag_context": rag_context,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    logger.info(f"Research Agent completed: {result.app_name}")
    return result


async def run_research_clarification(
    user_idea: str, target_audience: str = ""
) -> ClarificationResponse:
    """
    Research Agent clarification phase.

    Analyzes the user's app idea and generates targeted clarifying questions
    to gather more detail before generating the full requirements spec.

    Args:
        user_idea: The user's app idea description
        target_audience: Optional target audience description

    Returns:
        ClarificationResponse — questions for the user to answer

    Security:
        - Input passed through LangChain prompt template (no injection)
        - Output enforced via Pydantic schema
    """
    logger.info(f"Running Research Clarification for idea: {user_idea[:80]}...")

    llm = get_optimal_model("research")
    parser = PydanticOutputParser(pydantic_object=ClarificationResponse)

    system_prompt = get_agent_prompt("research_clarify")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "App Idea: {user_idea}\nTarget Audience: {target_audience}\n\n"
                "Identify the most important ambiguities and generate clarifying questions.",
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

    logger.info(f"Research Clarification completed: {len(result.questions)} questions")
    return result


async def run_research_with_context(
    user_idea: str,
    target_audience: str = "",
    clarifications: list = None,
) -> RequirementsDoc:
    """
    Research Agent with clarification context.

    Generates a requirements spec enriched with the user's answers
    to clarifying questions from the clarification phase.

    Args:
        user_idea: The user's app idea description
        target_audience: Optional target audience description
        clarifications: List of {question, answer} dicts from the user

    Returns:
        RequirementsDoc — Pydantic-enforced requirements spec

    Security:
        - Input passed through LangChain prompt template (no injection)
        - Output enforced via Pydantic schema
    """
    # Build clarification context string
    clarification_text = ""
    if clarifications:
        lines = []
        for item in clarifications:
            q = item.get("question", "")
            a = item.get("answer", "")
            lines.append(f"Q: {q}\nA: {a}")
        clarification_text = "\n\n".join(lines)

    logger.info(
        f"Running Research Agent with {len(clarifications or [])} clarifications "
        f"for idea: {user_idea[:80]}..."
    )

    llm = get_optimal_model("research")
    parser = PydanticOutputParser(pydantic_object=RequirementsDoc)

    system_prompt = get_agent_prompt("research")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            (
                "human",
                "App Idea: {user_idea}\nTarget Audience: {target_audience}\n\n"
                "Additional clarifications from the user:\n{clarifications}\n\n"
                "Analyze this idea with the additional context and generate "
                "a complete requirements specification.",
            ),
        ]
    )

    chain = prompt | llm | parser

    result = await chain.ainvoke(
        {
            "user_idea": user_idea,
            "target_audience": target_audience or "General users",
            "clarifications": clarification_text or "(none provided)",
            "format_instructions": parser.get_format_instructions(),
        }
    )

    logger.info(f"Research Agent with context completed: {result.app_name}")
    return result
