#!/usr/bin/env python3
"""Framework wiring smoke for the PydanticAI agent (pydantic-only; needs the
`pydantic` extra). Uses PydanticAI's TestModel/FunctionModel — no real LLM, no
API key, deterministic. Asserts the agent registers the tools and actually
invokes them (delegating to the shared run_tool), plus the multiply bonus.
Exits non-zero on failure so CI can gate on it."""
import json, sys
from app.agent_pydantic import agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel, AgentInfo
from pydantic_ai.messages import ModelResponse, ToolCallPart, TextPart


def make_script(tool, args):
    """Script: first turn calls `tool(args)`; once a tool-return is present,
    return it as final text so we can assert the executed tool's real result."""
    def script(messages, info: AgentInfo):
        ret = None
        for m in messages:
            for p in m.parts:
                if getattr(p, "part_kind", None) == "tool-return":
                    ret = p.content
        if ret is not None:
            return ModelResponse(parts=[TextPart(f"result={ret}")])
        return ModelResponse(parts=[ToolCallPart(tool_name=tool, args=args)])
    return script


failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

# TestModel: every registered tool is invoked (no API key, no real LLM).
testout = json.loads(agent.run_sync("hi", model=TestModel()).output)
check({"add", "time", "help", "multiply"} <= set(testout), f"tools registered/invoked, got {sorted(testout)}")

# FunctionModel: scripted add(19,23) -> framework executes add (via run_tool) -> 42.0
add_out = agent.run_sync("19 plus 23", model=FunctionModel(make_script("add", {"a": 19, "b": 23}))).output
check("42.0" in add_out, f"add via framework -> 42.0 (got {add_out!r})")

# Bonus: multiply was added with ONE decorator; scripted multiply(6,8) -> 48.0
mul_out = agent.run_sync("6 times 8", model=FunctionModel(make_script("multiply", {"a": 6, "b": 8}))).output
check("48.0" in mul_out, f"multiply (bonus) via framework -> 48.0 (got {mul_out!r})")

if failures:
    print("FAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print("OK: PydanticAI agent wiring + tools + multiply bonus verified")
