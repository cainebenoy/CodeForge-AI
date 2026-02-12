"""
LLM Model Router - Single source of truth for model selection
Routes each agent type to the optimal LangChain LLM instance
Optimizes cost vs. intelligence vs. context window
"""

from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logging import logger

AgentType = Literal["research", "wireframe", "code", "qa", "pedagogy", "roadmap"]


def get_optimal_model(agent_type: AgentType):
    """
    Route requests to the best LLM for the task.

    Strategy (per copilot-instructions.md):
    - Research/QA: GPT-4o (high reasoning for requirements analysis & code review)
    - Code: Gemini 1.5 Pro (1M token context window for full file awareness)
    - Wireframe: GPT-4o (structured architecture understanding)
    - Pedagogy/Roadmap: Claude 3.5 Sonnet (best at Socratic explanation & curriculum)

    Returns:
        LangChain ChatModel instance configured for the task
    """
    logger.debug(f"Selecting model for agent type: {agent_type}")

    if agent_type in ["research", "qa"]:
        # High intelligence tasks — reasoning & analysis
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )

    elif agent_type == "code":
        # Large context for full file awareness (1M tokens)
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    elif agent_type == "wireframe":
        # Structured output for architecture design
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.5,
            api_key=settings.OPENAI_API_KEY,
        )

    elif agent_type in ["pedagogy", "roadmap"]:
        # Socratic guidance & curriculum design — Claude excels here
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.8,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )

    else:
        # Fallback — default to GPT-4o for unknown types
        logger.warning(f"Unknown agent type '{agent_type}', falling back to GPT-4o")
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )
