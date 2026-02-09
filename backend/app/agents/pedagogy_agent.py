"""
Pedagogy Agent - "Socratic Mentor Persona"
Guides students through learning without giving direct answers
"""
from langchain.prompts import ChatPromptTemplate

from app.agents.core.llm import get_optimal_model


PEDAGOGY_AGENT_PROMPT = """You are a patient, Socratic coding mentor.

Student's question: {student_question}
Their current code: {student_code}

Your role:
1. Never give direct code answers
2. Ask guiding questions
3. Explain WHY, not just WHAT
4. Encourage experimentation
5. Celebrate progress

Respond with a helpful hint or question.
"""


async def run_pedagogy_agent(student_question: str, student_code: str) -> str:
    """
    Pedagogy Agent execution
    
    Returns: Socratic response (no direct answers)
    """
    llm = get_optimal_model("pedagogy")
    
    prompt = ChatPromptTemplate.from_template(PEDAGOGY_AGENT_PROMPT)
    
    chain = prompt | llm
    
    result = await chain.ainvoke({
        "student_question": student_question,
        "student_code": student_code,
    })
    
    return result.content
