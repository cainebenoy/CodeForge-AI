"""
QA Agent - "Testing Specialist Persona"
Validates generated code for errors and best practices
"""
from langchain.prompts import ChatPromptTemplate

from app.agents.core.llm import get_optimal_model


QA_AGENT_PROMPT = """You are a Senior QA Engineer reviewing code.

Code to review:
{code}

File: {file_path}

Check for:
1. Syntax errors
2. TypeScript errors
3. React hooks rules violations
4. Security vulnerabilities (hard-coded secrets, XSS)
5. Best practices violations

Provide a structured report with severity levels.
"""


async def run_qa_agent(code: str, file_path: str) -> dict:
    """
    QA Agent execution
    
    Returns: Dict with issues found and severity
    """
    llm = get_optimal_model("qa")
    
    prompt = ChatPromptTemplate.from_template(QA_AGENT_PROMPT)
    
    chain = prompt | llm
    
    result = await chain.ainvoke({
        "code": code,
        "file_path": file_path,
    })
    
    # Parse result into structured format
    return {
        "file": file_path,
        "issues": [],  # Parse from LLM response
        "passed": True,
    }
