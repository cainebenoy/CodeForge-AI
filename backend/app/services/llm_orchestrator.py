"""
LLM Model Router and Orchestration
Intelligently selects the best model for each task
Optimizes for cost vs capability and context requirements
"""
from typing import Optional, Dict, Any
import anthropic
import openai
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ExternalServiceError
from app.agents.prompts import get_agent_prompt


class ModelRouter:
    """Routes LLM calls to optimal models based on task type"""

    # Model selection strategy
    MODELS = {
        "research": "gpt-4o",  # High reasoning for requirements analysis
        "wireframe": "gpt-4o",  # Architecture understanding
        "code": "gemini-1.5-pro",  # Large context window (1M tokens) for full file awareness
        "qa": "gpt-4o-mini",  # Fast review, lower cost
        "pedagogy": "claude-3-5-sonnet",  # Best at Socratic explanation
        "routing": "gpt-4o-mini",  # Fast classification
    }

    # Context limits per model (tokens)
    CONTEXT_LIMITS = {
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gemini-1.5-pro": 1000000,  # 1M context window
        "claude-3-5-sonnet": 200000,
    }

    @classmethod
    def get_model_for_agent(cls, agent_type: str) -> str:
        """Get optimal model for agent type"""
        return cls.MODELS.get(agent_type, "gpt-4o")

    @classmethod
    def get_context_limit(cls, model: str) -> int:
        """Get context limit for model"""
        return cls.CONTEXT_LIMITS.get(model, 128000)


class LLMOrchestrator:
    """Orchestrates LLM calls with error handling and retries"""

    def __init__(self):
        """Initialize LLM clients"""
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def call_gpt4(
        self,
        messages: list,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Call OpenAI GPT-4 models
        """
        try:
            logger.info(f"Calling {model} with {len(messages)} messages")

            kwargs = {
                "messages": messages,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            # JSON mode for structured outputs
            if response_format:
                kwargs["response_format"] = response_format

            response = await self.openai_client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content
            logger.info(f"Received response from {model}: {len(content)} chars")
            return content

        except openai.RateLimitError as e:
            logger.error(f"Rate limit exceeded for {model}")
            raise ExternalServiceError("OpenAI", "Rate limit exceeded") from e
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise ExternalServiceError("OpenAI", str(e)) from e

    async def call_claude(
        self,
        messages: list,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Call Anthropic Claude models
        """
        try:
            logger.info(f"Calling {model} with {len(messages)} messages")

            response = self.anthropic_client.messages.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.content[0].text
            logger.info(f"Received response from {model}: {len(content)} chars")
            return content

        except anthropic.RateLimitError as e:
            logger.error(f"Rate limit exceeded for {model}")
            raise ExternalServiceError("Anthropic", "Rate limit exceeded") from e
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise ExternalServiceError("Anthropic", str(e)) from e

    async def call_agent_llm(
        self,
        agent_type: str,
        user_input: str,
        context: Dict[str, Any],
        temperature: float = 0.7,
    ) -> str:
        """
        Call the appropriate LLM for an agent
        Automatically selects model and formats messages
        """
        model = ModelRouter.get_model_for_agent(agent_type)
        system_prompt = get_agent_prompt(agent_type)

        # Format context into the message
        context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"{user_input}\n\nContext:\n{context_str}",
            },
        ]

        if "gpt" in model:
            return await self.call_gpt4(messages, model=model, temperature=temperature)
        elif "claude" in model:
            return await self.call_claude(messages, model=model, temperature=temperature)
        else:
            # Gemini not yet supported - fallback to GPT-4
            logger.warning(f"Model {model} not yet implemented, falling back to gpt-4o")
            return await self.call_gpt4(messages, model="gpt-4o", temperature=temperature)
