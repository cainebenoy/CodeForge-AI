"""
Code Agent - "Senior Developer Persona"
Generates production-ready code files
"""
from langchain.prompts import ChatPromptTemplate

from app.agents.core.llm import get_optimal_model


CODE_AGENT_PROMPT = """You are a Senior Full-Stack Developer writing production code.

Architecture:
{architecture}

File to generate: {file_path}

Requirements:
- Write clean, idiomatic code
- Follow the specified architecture
- Use TypeScript strict mode
- Include error handling
- Add JSDoc comments for complex logic
- NEVER hard-code API keys (use process.env.VARIABLE)

Generate the complete file content.
"""


async def run_code_agent(architecture: str, file_path: str) -> str:
    """
    Code Agent execution
    
    Uses Gemini 1.5 Pro for large context awareness
    Returns: Complete file content as string
    """
    llm = get_optimal_model("code")
    
    prompt = ChatPromptTemplate.from_template(CODE_AGENT_PROMPT)
    
    chain = prompt | llm
    
    result = await chain.ainvoke({
        "architecture": architecture,
        "file_path": file_path,
    })
    
    return result.content
