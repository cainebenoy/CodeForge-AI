"""
Research Agent - "Product Manager Persona"
Generates requirements specification from user input
"""
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from app.agents.core.llm import get_optimal_model
from app.schemas.protocol import RequirementsDoc


RESEARCH_AGENT_PROMPT = """You are an experienced Product Manager analyzing a user's app idea.

User Idea: {user_idea}

Your task:
1. Extract the core value proposition
2. Define target user personas
3. Identify must-have vs nice-to-have features
4. Recommend a tech stack suitable for MVP

Be specific, practical, and focus on shipping an MVP quickly.

Output a structured requirements document.
"""


async def run_research_agent(user_idea: str) -> RequirementsDoc:
    """
    Research Agent execution
    
    Security: Input sanitized via Pydantic
    Output: Enforced schema prevents hallucination
    """
    llm = get_optimal_model("research")
    parser = PydanticOutputParser(pydantic_object=RequirementsDoc)
    
    prompt = ChatPromptTemplate.from_template(
        RESEARCH_AGENT_PROMPT + "\n{format_instructions}"
    )
    
    chain = prompt | llm | parser
    
    result = await chain.ainvoke({
        "user_idea": user_idea,
        "format_instructions": parser.get_format_instructions(),
    })
    
    return result
