import asyncio, json, httpx
from . import config
from .tools import TOOL_SCHEMAS, run_tool

MAX_TOOL_ITERS = 4


async def ask_ai(message: str) -> str:
    if config.AI_PROVIDER == "echo":
        return "Echo: " + message
    if config.AI_PROVIDER == "claude-cli":
        return await run_cli(["claude", "-p", message])
    if config.AI_PROVIDER == "gemini-cli":
        return await run_cli(["gemini", "-p", message])
    if config.AI_PROVIDER == "http":
        return await run_http_agent(message)
    if config.AI_PROVIDER == "pydantic":
        # Part 2: the PydanticAI agent. Lazy import so base (non-pydantic)
        # installs never require pydantic-ai.
        from .agent_pydantic import run_pydantic_agent
        return await run_pydantic_agent(message)
    return "Unsupported AI_PROVIDER"


async def run_http_agent(message: str) -> str:
    """OpenAI-compatible chat-completions tool-calling loop.

    Sends the conversation plus `tools=TOOL_SCHEMAS`. If the model replies with
    `tool_calls`, each is executed via run_tool and the result is appended as a
    `role:"tool"` message (with the matching tool_call_id); we then loop until
    the model returns a plain text answer or we hit MAX_TOOL_ITERS.
    """
    headers = {"Authorization": "Bearer " + config.HTTP_LLM_API_KEY} if config.HTTP_LLM_API_KEY else {}
    messages = [{"role": "user", "content": message}]
    async with httpx.AsyncClient(timeout=60) as c:
        for _ in range(MAX_TOOL_ITERS):
            payload = {
                "model": config.MODEL_NAME,
                "messages": messages,
                "tools": TOOL_SCHEMAS,
            }
            r = await c.post(config.HTTP_LLM_ENDPOINT, json=payload, headers=headers)
            r.raise_for_status()
            choice = r.json()["choices"][0]["message"]
            tool_calls = choice.get("tool_calls")
            if not tool_calls:
                return choice.get("content") or ""
            # Echo the assistant turn that requested the tools, then answer each.
            messages.append(choice)
            for call in tool_calls:
                fn = call["function"]
                name = fn["name"]
                try:
                    arguments = json.loads(fn.get("arguments") or "{}")
                except (json.JSONDecodeError, TypeError):
                    arguments = {}
                result = await run_tool(name, arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": name,
                    "content": result,
                })
        # Tool budget exhausted: do a final plain (no-tools) call for an answer.
        payload = {"model": config.MODEL_NAME, "messages": messages}
        r = await c.post(config.HTTP_LLM_ENDPOINT, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"].get("content") or ""


async def run_cli(cmd):
    p = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await p.communicate()
    return out.decode(errors="replace").strip() if p.returncode == 0 else err.decode(errors="replace")[-1200:]
