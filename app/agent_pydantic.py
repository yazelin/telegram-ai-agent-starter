"""PydanticAI version of the hand-rolled tool-loop in app/agent.py:run_http_agent.

The framework owns the loop, tool dispatch, message bookkeeping, and JSON-schema
generation. Tools are registered with one @agent.tool_plain decorator each and
delegate to the shared app/tools.py:run_tool, so behavior matches the hand-rolled
version while removing the TOOL_SCHEMAS + manual-loop boilerplate. Requires the
`pydantic` extra: uv sync --extra pydantic."""
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from . import config
from .tools import run_tool

agent = Agent(system_prompt="You are a helpful Telegram assistant. Use tools when relevant.")


@agent.tool_plain
async def time() -> str:
    """Return the current local date and time in ISO 8601 format."""
    return await run_tool("time", {})


@agent.tool_plain
async def help() -> str:
    """Return a short usage hint for this bot."""
    return await run_tool("help", {})


@agent.tool_plain
async def add(a: float, b: float) -> str:
    """Add two numbers and return the sum."""
    return await run_tool("add", {"a": a, "b": b})


# BONUS (framework-only): adding a tool is ONE decorator + a typed function.
# Compare the hand-rolled version, where a new tool means editing TOOL_SCHEMAS
# (hand-written JSON schema) AND run_tool (dispatch) in two separate places.
@agent.tool_plain
async def multiply(a: float, b: float) -> str:
    """Multiply two numbers and return the product."""
    return str(a * b)


async def run_pydantic_agent(message: str) -> str:
    """Run the agent against the configured OpenAI-compatible endpoint.

    HTTP_LLM_ENDPOINT in this repo is the full .../v1/chat/completions URL; the
    PydanticAI OpenAI provider wants the base (.../v1), so strip the suffix."""
    base = config.HTTP_LLM_ENDPOINT.removesuffix("/chat/completions")
    model = OpenAIChatModel(
        config.MODEL_NAME,
        provider=OpenAIProvider(base_url=base, api_key=config.HTTP_LLM_API_KEY or "x"),
    )
    result = await agent.run(message, model=model)
    return result.output
