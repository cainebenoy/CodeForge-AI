"""
LLM Model Router - selects optimal model for each task
Optimizes cost vs. intelligence
"""
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

from app.core.config import settings

AgentType = Literal["research", "wireframe", "code", "qa", "pedagogy"]


def get_optimal_model(agent_type: AgentType):
    """
    Route requests to the best LLM for the task
    
    Strategy:
    - Research/QA: GPT-4o or Claude (high reasoning)
    - Code: Gemini 1.5 Pro (large context ~1M tokens)
    - Routing: Gemini Flash (cheap, fast)
    """
    
    if agent_type in ["research", "qa"]:
        # High intelligence tasks
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )
    
    elif agent_type == "code":
        # Large context for full file awareness
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.3,
            google_api_key=settings.GOOGLE_API_KEY,
        )
    
    elif agent_type == "wireframe":
        # Structured output
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.5,
            api_key=settings.OPENAI_API_KEY,
        )
    
    else:  # pedagogy
        # Socratic guidance
        return ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            temperature=0.8,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )
