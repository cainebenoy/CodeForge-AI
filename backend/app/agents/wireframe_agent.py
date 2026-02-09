"""
Wireframe Agent - "System Architect Persona"
Generates application architecture and component tree
"""
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from app.agents.core.llm import get_optimal_model
from app.schemas.protocol import WireframeSpec


WIREFRAME_AGENT_PROMPT = """You are a Senior System Architect designing an application.

Requirements:
{requirements}

Your task:
1. Design the site map (routes)
2. Break down each page into components
3. Identify global state needs
4. Choose a color theme

Be practical and follow modern web app patterns.

Output a structured wireframe specification.
"""


async def run_wireframe_agent(requirements: str) -> WireframeSpec:
    """
    Wireframe Agent execution
    
    Input: Requirements from Research Agent
    Output: Architecture specification with Pydantic validation
    """
    llm = get_optimal_model("wireframe")
    parser = PydanticOutputParser(pydantic_object=WireframeSpec)
    
    prompt = ChatPromptTemplate.from_template(
        WIREFRAME_AGENT_PROMPT + "\n{format_instructions}"
    )
    
    chain = prompt | llm | parser
    
    result = await chain.ainvoke({
        "requirements": requirements,
        "format_instructions": parser.get_format_instructions(),
    })
    
    return result
