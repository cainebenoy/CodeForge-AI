"""
Agent Orchestrator - coordinates agent workflows
Routes requests to appropriate agents with error handling and timeout management
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.schemas.protocol import AgentRequest
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import AgentExecutionError
from app.services.database import DatabaseOperations
from app.services.llm_orchestrator import LLMOrchestrator


async def run_agent_workflow(
    job_id: str,
    request: AgentRequest,
) -> Optional[Dict[str, Any]]:
    """
    Execute agent workflow asynchronously with proper error handling and timeouts

    Args:
        job_id: Unique job identifier
        request: Agent request with type and context

    Returns:
        Agent result dictionary (schema depends on agent type)

    Security:
        - All inputs validated via Pydantic schema
        - Timeouts prevent resource exhaustion (5 min max)
        - Error messages sanitized (no stack traces to client)
        - Database operations use RLS

    Timeouts:
        - Research Agent: 180s
        - Wireframe Agent: 240s
        - Code Agent: 300s
        - QA Agent: 120s
        - Pedagogy Agent: 120s
    """
    logger.info(f"Starting agent workflow: job={job_id}, type={request.agent_type}")

    try:
        # Initialize LLM orchestrator
        llm = LLMOrchestrator()

        # Route to appropriate agent with timeout
        if request.agent_type == "research":
            result = await asyncio.wait_for(
                _run_research_agent(llm, request),
                timeout=180,
            )
        elif request.agent_type == "wireframe":
            result = await asyncio.wait_for(
                _run_wireframe_agent(llm, request),
                timeout=240,
            )
        elif request.agent_type == "code":
            result = await asyncio.wait_for(
                _run_code_agent(llm, request),
                timeout=300,
            )
        elif request.agent_type == "qa":
            result = await asyncio.wait_for(
                _run_qa_agent(llm, request),
                timeout=120,
            )
        elif request.agent_type == "pedagogy":
            result = await asyncio.wait_for(
                _run_pedagogy_agent(llm, request),
                timeout=120,
            )
        else:
            raise ValueError(f"Unknown agent type: {request.agent_type}")

        # Store result in database
        await DatabaseOperations.update_project(
            request.project_id,
            {
                "status": f"{request.agent_type}_complete",
                f"{request.agent_type}_result": result,
            },
        )

        logger.info(f"Agent workflow completed: job={job_id}")
        return result

    except asyncio.TimeoutError:
        error_msg = f"Agent execution timeout ({settings.AGENT_TIMEOUT}s)"
        logger.error(f"Timeout for job {job_id}: {error_msg}")
        raise AgentExecutionError(request.agent_type, error_msg)

    except Exception as e:
        error_msg = f"Agent execution failed: {str(e)}"
        logger.error(f"Error in job {job_id}: {error_msg}")
        raise AgentExecutionError(request.agent_type, error_msg)


async def _run_research_agent(llm: LLMOrchestrator, request: AgentRequest) -> Dict[str, Any]:
    """
    Research Agent: Analyze idea and generate requirements
    Output: RequirementsDoc schema
    """
    logger.info(f"Running Research Agent for project {request.project_id}")

    user_idea = request.input_context.get("user_idea", "")
    target_audience = request.input_context.get("target_audience", "")

    prompt = f"""Analyze this app idea and generate a requirements specification.

App Idea: {user_idea}
Target Audience: {target_audience}

Generate a JSON response matching this structure:
{{
  "app_name": "string",
  "elevator_pitch": "string (20-500 chars)",
  "target_audience": [
    {{"role": "user role", "goal": "what they want to achieve", "pain_point": "their problem"}}
  ],
  "core_features": [
    {{"name": "feature name", "description": "what it does", "priority": "must-have|should-have|nice-to-have"}}
  ],
  "recommended_stack": ["technology1", "technology2"],
  "technical_constraints": "optional notes"
}}"""

    response = await llm.call_agent_llm(
        agent_type="research",
        user_input=prompt,
        context={"user_idea": user_idea},
        temperature=0.7,
    )

    # Parse response as JSON
    import json
    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON response from Research Agent, using raw response")
        result = {"raw_response": response}

    return result


async def _run_wireframe_agent(llm: LLMOrchestrator, request: AgentRequest) -> Dict[str, Any]:
    """
    Wireframe Agent: Design architecture and component structure
    Output: WireframeSpec schema
    """
    logger.info(f"Running Wireframe Agent for project {request.project_id}")

    requirements = request.input_context.get("requirements", "")

    prompt = f"""Design the architecture for this app based on requirements.

Requirements: {requirements}

Generate a JSON response with:
{{
  "site_map": [
    {{
      "path": "/route",
      "description": "page description",
      "components": [
        {{"name": "ComponentName", "props": ["props"], "children": ["child components"]}}
      ]
    }}
  ],
  "global_state_needs": ["state entities"],
  "theme_colors": ["#hexcolor1", "#hexcolor2"]
}}"""

    response = await llm.call_agent_llm(
        agent_type="wireframe",
        user_input=prompt,
        context={"requirements": requirements},
        temperature=0.5,
    )

    import json
    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON response from Wireframe Agent")
        result = {"raw_response": response}

    return result


async def _run_code_agent(llm: LLMOrchestrator, request: AgentRequest) -> Dict[str, Any]:
    """
    Code Agent: Generate production-ready code
    Uses Gemini 1.5 Pro for large context window awareness
    """
    logger.info(f"Running Code Agent for project {request.project_id}")

    architecture = request.input_context.get("architecture", "")
    component_specs = request.input_context.get("components", [])

    prompt = f"""Generate production-ready TypeScript/React code.

Architecture: {architecture}
Components to generate: {component_specs}

Generate code that is:
- Type-safe with strict TypeScript
- Follows React best practices
- Includes error handling
- Has JSDoc comments
- Uses semantic HTML
- Follows accessibility standards"""

    response = await llm.call_agent_llm(
        agent_type="code",
        user_input=prompt,
        context={"architecture": architecture},
        temperature=0.3,
    )

    return {"generated_code": response}


async def _run_qa_agent(llm: LLMOrchestrator, request: AgentRequest) -> Dict[str, Any]:
    """
    QA Agent: Review code for quality and security
    Output: List of issues with severity levels
    """
    logger.info(f"Running QA Agent for project {request.project_id}")

    code = request.input_context.get("code", "")

    prompt = f"""Review this code for production readiness.

Code:
{code}

Check for:
- Type safety violations
- Security vulnerabilities
- Performance issues
- Error handling coverage
- Accessibility issues

Report each issue with severity: CRITICAL, HIGH, MEDIUM, LOW"""

    response = await llm.call_agent_llm(
        agent_type="qa",
        user_input=prompt,
        context={"code_length": len(code)},
        temperature=0.5,
    )

    return {"review_report": response}


async def _run_pedagogy_agent(llm: LLMOrchestrator, request: AgentRequest) -> Dict[str, Any]:
    """
    Pedagogy Agent: Guide student learning with Socratic method
    Output: Guided learning steps and questions
    """
    logger.info(f"Running Pedagogy Agent for project {request.project_id}")

    student_question = request.input_context.get("question", "")
    topic = request.input_context.get("topic", "")

    prompt = f"""Help a student learn about {topic} using the Socratic method.

Student's Question: {student_question}

Respond by:
1. Asking clarifying questions (don't give answers directly)
2. Guiding them to think through the problem
3. Explaining the WHY behind concepts
4. Providing hints, not solutions
5. Encouraging experimentation"""

    response = await llm.call_agent_llm(
        agent_type="pedagogy",
        user_input=prompt,
        context={"topic": topic},
        temperature=0.8,
    )

    return {"guidance": response}
