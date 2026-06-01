from datetime import datetime

# OpenAI-style function/tool schemas. The http provider sends this list as
# `tools=` so the LLM can decide to call them. Keep each schema's `name`
# aligned with a branch in run_tool below.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "time",
            "description": "Return the current local date and time in ISO 8601 format.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "help",
            "description": "Return a short usage hint for this bot.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


async def run_tool(name: str, arguments: dict | None = None) -> str:
    """Dispatch a tool by name. `arguments` is the parsed argument dict
    (from /tool REST text or from the LLM's tool_call arguments)."""
    arguments = arguments or {}
    if name == "time":
        return datetime.now().astimezone().isoformat(timespec="seconds")
    if name == "help":
        return "Try /ask your question or /tool time"
    return f"Unknown tool: {name}"
