#!/usr/bin/env python3
"""Tool-logic unit smoke (base deps, no extra). The shared run_tool is what both
the hand-rolled loop and the PydanticAI tools call, so verifying it here covers
the behavior both tracks depend on. Exits non-zero on failure."""
import asyncio, sys
from app.tools import run_tool


async def main():
    failures = []
    def check(cond, label):
        if not cond:
            failures.append(label)

    add = await run_tool("add", {"a": 19, "b": 23})
    check(add == "42.0", f"add(19,23) -> '42.0' (got {add!r})")
    check(await run_tool("add", {"a": "x"}) == "add needs numeric arguments a and b", "add bad args -> message")
    t = await run_tool("time", {})
    check("T" in t and ":" in t, f"time -> ISO-ish (got {t!r})")
    check(await run_tool("help", {}) == "Try /ask your question or /tool time", "help -> hint")
    check(await run_tool("nope", {}) == "Unknown tool: nope", "unknown -> message")

    if failures:
        print("FAIL:", "; ".join(failures), file=sys.stderr)
        sys.exit(1)
    print("OK: tool-logic smoke passed")


asyncio.run(main())
