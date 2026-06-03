# PydanticAI Agent Comparison Second-Half Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second course track that reimplements the hand-rolled OpenAI tool-loop with a PydanticAI Agent, as a contrast lesson, with deterministic API-key-free tests.

**Architecture:** Keep `app/agent.py:run_http_agent` (hand-rolled loop) unchanged. Add `app/agent_pydantic.py` — a PydanticAI Agent whose tools (`@agent.tool_plain`) delegate to the shared `app/tools.py:run_tool`, so behavior matches while the framework owns the loop, dispatch, message bookkeeping, and JSON-schema generation. PydanticAI is an optional `pydantic` extra; `app/agent.py:ask_ai` routes to it when `AI_PROVIDER=pydantic` (lazy import). Tests use PydanticAI's TestModel/FunctionModel (no real LLM, no API key).

**Tech Stack:** Python 3.10+, uv, pydantic-ai-slim[openai] 1.x (optional extra), GitHub Actions. No pytest — plain-python smoke scripts (family style).

---

## Preconditions / verified facts

Scratch-verified against **pydantic-ai 1.105.0 via `pydantic-ai-slim[openai]` (~30 packages, much lighter than full pydantic-ai's ~147)**:
- `from pydantic_ai import Agent`; `@agent.tool_plain` registers a typed function as a tool (schema auto-generated from the signature).
- Async tool wrappers that `await run_tool(...)` work: `add(19,23)` → `"42.0"`, `time()` → real ISO string, `help()` → the real hint.
- `from pydantic_ai.models.test import TestModel`: `agent.run_sync("hi", model=TestModel()).output` is a JSON string of `{tool: result}` for ALL registered tools (proves the framework invokes them; no API key).
- `from pydantic_ai.models.function import FunctionModel, AgentInfo` + `from pydantic_ai.messages import ModelResponse, ToolCallPart, TextPart`: a scripted FunctionModel that returns `ToolCallPart(tool_name="add", args={"a":19,"b":23})` then (once a tool-return is present) `TextPart(...)` causes the framework to execute the real tool. Verified final output reflected the executed tool.
- Real endpoint wiring: `from pydantic_ai.models.openai import OpenAIChatModel` + `from pydantic_ai.providers.openai import OpenAIProvider`; `OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=..., api_key=...))` constructs cleanly (tests do NOT need this — they use Test/FunctionModel).
- `run_tool("add", {"a":19,"b":23})` returns the string `"42.0"` (float sum). `run_tool("nope")` → `"Unknown tool: nope"`.

**Working dir:** `/home/ct/telegram-ai-agent-starter`. Branch `feat/pydantic-ai-agent-track` (not main).

---

## File structure

| File | Responsibility |
|---|---|
| `pyproject.toml` (modify) | `pydantic` optional extra |
| `app/agent_pydantic.py` (create) | PydanticAI Agent + tool wrappers + multiply bonus + `run_pydantic_agent` |
| `app/agent.py` (modify) | `AI_PROVIDER=pydantic` lazy branch in `ask_ai` |
| `tools_smoke_test.py` (create) | base-deps unit smoke for `run_tool` |
| `agent_smoke_test_pydantic.py` (create) | pydantic-track framework wiring smoke (Test/FunctionModel) |
| `.github/workflows/ci.yml` (create) | matrix: base + pydantic |
| `docs/08-pydantic-ai-agent.md` (create) | the lesson |
| `docs/00-overview.md`, `tutorial.html`, `README.md`, `index.html`, `DESIGN.md` (modify) | two-track framing |

---

## Task 1: Add the pydantic optional extra

**Files:** Modify `pyproject.toml`; regenerate `uv.lock`.

- [ ] **Step 1: Edit `pyproject.toml`** — add after the existing `dependencies = [...]` array (keep `[tool.uv] package = false`; do NOT add pydantic-ai to required deps):

```toml
[project.optional-dependencies]
pydantic = ["pydantic-ai-slim[openai]>=1,<2"]
```

- [ ] **Step 2: Regenerate lock + confirm base excludes pydantic_ai.**

Run: `uv lock && uv sync && uv run python -c "import importlib.util as u; print('pydantic_ai:', u.find_spec('pydantic_ai') is not None)"`
Expected: `pydantic_ai: False`.

- [ ] **Step 3: Confirm the extra installs pydantic-ai 1.x.**

Run: `uv sync --extra pydantic && uv run python -c "import pydantic_ai; print(pydantic_ai.__version__)"`
Expected: `1.x` (likely 1.105.x).

- [ ] **Step 4: Restore base env.**

Run: `uv sync`

- [ ] **Step 5: Commit.**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add optional pydantic extra (pydantic-ai-slim[openai])"
```

---

## Task 2: Tool-logic unit smoke (base deps)

**Files:** Create `tools_smoke_test.py`.

- [ ] **Step 1: Create `tools_smoke_test.py`** (base deps, no extra — characterizes the shared `run_tool` both tracks depend on):

```python
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
```

- [ ] **Step 2: Run it on base deps — must pass (run_tool already exists).**

Run: `uv sync && PYTHONPATH=. uv run python tools_smoke_test.py`
Expected: `OK: tool-logic smoke passed`, exit 0.

- [ ] **Step 3: Commit.**

```bash
git add tools_smoke_test.py
git commit -m "test: add base tool-logic smoke for run_tool"
```

---

## Task 3: PydanticAI agent + framework wiring smoke

**Files:** Create `app/agent_pydantic.py`, `agent_smoke_test_pydantic.py`.

- [ ] **Step 1: Write the framework wiring smoke (this is the test).** Create `agent_smoke_test_pydantic.py`:

```python
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
```

- [ ] **Step 2: Run it to verify it FAILS (agent_pydantic missing).**

Run: `uv sync --extra pydantic && PYTHONPATH=. uv run python agent_smoke_test_pydantic.py; echo "exit=$?"`
Expected: non-zero exit — `ModuleNotFoundError: No module named 'app.agent_pydantic'`.

- [ ] **Step 3: Create `app/agent_pydantic.py`:**

```python
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
```

- [ ] **Step 4: Run the wiring smoke — must PASS.**

Run: `PYTHONPATH=. uv run python agent_smoke_test_pydantic.py`
Expected: `OK: PydanticAI agent wiring + tools + multiply bonus verified`, exit 0.

- [ ] **Step 5: Confirm the base tool smoke still passes (no regression).**

Run: `uv sync && PYTHONPATH=. uv run python tools_smoke_test.py`
Expected: `OK: tool-logic smoke passed`.

- [ ] **Step 6: Commit.**

```bash
git add app/agent_pydantic.py agent_smoke_test_pydantic.py
git commit -m "feat: PydanticAI agent (tools delegate to run_tool) + wiring smoke + multiply bonus"
```

---

## Task 4: Wire AI_PROVIDER=pydantic into ask_ai

**Files:** Modify `app/agent.py`.

- [ ] **Step 1: Edit `app/agent.py`** — add a `pydantic` branch in `ask_ai`, with a LAZY import so the base import chain never needs pydantic-ai. Change the `ask_ai` function from:

```python
async def ask_ai(message: str) -> str:
    if config.AI_PROVIDER == "echo":
        return "Echo: " + message
    if config.AI_PROVIDER == "claude-cli":
        return await run_cli(["claude", "-p", message])
    if config.AI_PROVIDER == "gemini-cli":
        return await run_cli(["gemini", "-p", message])
    if config.AI_PROVIDER == "http":
        return await run_http_agent(message)
    return "Unsupported AI_PROVIDER"
```

to:

```python
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
```

Do NOT change `run_http_agent`, `run_cli`, or anything else in the file.

- [ ] **Step 2: Verify base import works without pydantic-ai (default/echo path).**

Run: `uv sync && PYTHONPATH=. uv run python -c "import app.agent; import importlib.util as u; print('agent imports on base:', True, '| pydantic_ai present:', u.find_spec('pydantic_ai') is not None)"`
Expected: `agent imports on base: True | pydantic_ai present: False` (lazy import keeps base clean).

- [ ] **Step 3: Verify echo path still works (base).**

Run: `PYTHONPATH=. uv run python -c "
import asyncio, os; os.environ['AI_PROVIDER']='echo'
from app.agent import ask_ai
print(asyncio.run(ask_ai('hello')))
"`
Expected: `Echo: hello`.

- [ ] **Step 4: Commit.**

```bash
git add app/agent.py
git commit -m "feat: route AI_PROVIDER=pydantic to the PydanticAI agent (lazy import)"
```

---

## Task 5: CI matrix (base + pydantic)

**Files:** Create `.github/workflows/ci.yml`.

- [ ] **Step 1: Create `.github/workflows/ci.yml`:**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        track: [base, pydantic]
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5

      # base track: no extra, hand-rolled agent + shared tools
      - name: Sync (base)
        if: matrix.track == 'base'
        run: uv sync
      - name: Tool-logic smoke
        if: matrix.track == 'base'
        run: PYTHONPATH=. uv run python tools_smoke_test.py

      # pydantic track: installs the extra, runs the framework wiring smoke
      - name: Sync with pydantic extra
        if: matrix.track == 'pydantic'
        run: uv sync --extra pydantic
      - name: PydanticAI agent wiring smoke
        if: matrix.track == 'pydantic'
        run: PYTHONPATH=. uv run python agent_smoke_test_pydantic.py
```

- [ ] **Step 2: Validate YAML.**

Run: `uv run --with pyyaml python -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml ok', d['jobs']['smoke-test']['strategy']['matrix']['track'])"`
Expected: `yaml ok ['base', 'pydantic']`.

- [ ] **Step 3: Locally simulate both tracks.**

Run:
```bash
uv sync && PYTHONPATH=. uv run python tools_smoke_test.py
uv sync --extra pydantic && PYTHONPATH=. uv run python agent_smoke_test_pydantic.py
uv sync
```
Expected: two `OK:` lines.

- [ ] **Step 4: Commit.**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: matrix runs base + pydantic tracks (tools smoke + agent wiring smoke)"
```

---

## Task 6: Write the lesson `docs/08-pydantic-ai-agent.md`

**Files:** Create `docs/08-pydantic-ai-agent.md`.

- [ ] **Step 1: Create the file** with this content (Traditional Chinese; no emoji):

````markdown
# Telegram AI Agent 入門模板：用 PydanticAI 重寫 agent(對照組)

前半段(`01`/`03`)你已經**手刻**了一個 OpenAI 相容的 tool-calling 迴圈(`app/agent.py` 的 `run_http_agent`):自己組 `messages`、`for _ in range(MAX_TOOL_ITERS)` 迴圈、手讀 `tool_calls`、手 dispatch `run_tool`、手接 `role:"tool"`。工具還是 `app/tools.py` 的 `TOOL_SCHEMAS`(手寫 JSON schema)+ `run_tool`(dispatch)**兩處維護**。它能動、看得懂,但樣板很多。這一段是課程後半:用 **PydanticAI** agent 框架重寫同一個 agent。

獨立的一課 —— 先跑過前半段、體會手刻迴圈的繁瑣,再回來看這段最有感。

## 先講結論:差在哪

| 面向 | 手刻(`app/agent.py`) | PydanticAI(`app/agent_pydantic.py`) |
|---|---|---|
| tool-loop | 手寫 `for _ in range(MAX_TOOL_ITERS)` + 手接 `role:tool` | 框架擁有迴圈 |
| 工具註冊 | `TOOL_SCHEMAS`(手寫 JSON)+ `run_tool` 兩處 | `@agent.tool_plain` 一個 decorator;schema 由型別自動生 |
| 工具邏輯 | `run_tool` | **共用**:框架工具是 typed wrapper 呼叫 `run_tool` |
| 加一個工具 | 改 `TOOL_SCHEMAS` + `run_tool` 兩處 | 加一個 `@agent.tool_plain` 函式 |

核心訊息:**框架移除的是「手寫 schema + 手刻迴圈」,不是你的工具邏輯** —— PydanticAI 的工具是薄 wrapper 呼叫既有 `run_tool`,所以兩版行為一致,而樣板少一大截。

## 步驟 1:裝 PydanticAI

```bash
uv sync --extra pydantic
```

成功的話 `uv run python -c "import pydantic_ai; print(pydantic_ai.__version__)"` 會印出 `1.x`。我們用 `pydantic-ai-slim[openai]`(只帶 OpenAI provider,比完整 `pydantic-ai` 輕很多)。

## 步驟 2:看 `app/agent_pydantic.py`

工具就是一個帶 type hints 的函式 + 一個 decorator,schema 由 PydanticAI 從型別自動生:

```python
from pydantic_ai import Agent
from .tools import run_tool

agent = Agent(system_prompt="You are a helpful Telegram assistant. Use tools when relevant.")

@agent.tool_plain
async def add(a: float, b: float) -> str:
    """Add two numbers and return the sum."""
    return await run_tool("add", {"a": a, "b": b})
```

對照手刻版:你不用寫 `TOOL_SCHEMAS` 的 JSON、不用 `for _ in range(MAX_TOOL_ITERS)` 手刻迴圈、不用手接 `role:"tool"` 訊息。框架看型別自動生 schema、自動跑工具迴圈。

## 步驟 3:跑框架接線 smoke(確定性、免 API key)

agent loop 本來要 LLM 決定呼叫哪個工具 —— 那是非確定的。PydanticAI 內建 `TestModel` / `FunctionModel` 讓你**不打真 LLM、不需要 API key**就能確定性地驅動 agent 並真的觸發工具:

```bash
uv sync --extra pydantic
PYTHONPATH=. uv run python agent_smoke_test_pydantic.py
```

它斷言:`TestModel` 會把所有註冊工具都叫一遍(證明框架接線正確);`FunctionModel` 腳本化「叫 `add(19,23)`」→ 框架執行 add(經 `run_tool`)→ 結果 `42.0`。成功會看到 `OK: PydanticAI agent wiring + tools + multiply bonus verified`。

> 對比 mcp / linebot:那兩課證明兩種寫法「行為相同」用的是真傳輸 + 本地假 server。這裡 agent 要 LLM 決策,改用框架內建的測試 model,更輕也更確定。

## 步驟 4:框架才給得起的紅利 —— 加工具一行 decorator

手刻版要加一個工具,得改 `TOOL_SCHEMAS`(寫一段 JSON schema)**和** `run_tool`(加一個分支)兩個地方。框架版只要一個 decorator:

```python
@agent.tool_plain
async def multiply(a: float, b: float) -> str:
    """Multiply two numbers and return the product."""
    return str(a * b)
```

smoke test 用 `FunctionModel` 腳本叫 `multiply(6,8)` → 斷言 `48.0`,證明新工具自動有 schema、自動進迴圈,不用碰任何 dispatch 表。

## 步驟 5:在真 bot 切換

`ask_ai` 用 `AI_PROVIDER` 切換,設 `pydantic` 就改走框架版 agent:

```bash
uv sync --extra pydantic
# .env: AI_PROVIDER=pydantic, 並設好 HTTP_LLM_ENDPOINT / HTTP_LLM_API_KEY / MODEL_NAME
uv run uvicorn app.main:app
```

工具與回答行為不變 —— 只是迴圈與 schema 改由框架管理。

## 何時用框架

- **手刻**(前半段):學習、看懂 tool-calling 迴圈到底在做什麼、極簡或不想帶框架相依。
- **PydanticAI**(這一段):工具一多、要型別驗證 / 結構化輸出 / 多步驟、長期維護 —— 少寫一堆樣板,專注在工具與商業邏輯。

下一步若要再進階:結構化輸出(回傳 Pydantic model)、多 agent 交接(handoff)、對話記憶、可觀測性(tracing)。本課把最小可動的框架版做到能跑、能對照,先把概念站穩。
````

- [ ] **Step 2: Verify the doc's commands work.**

Run: `uv sync --extra pydantic && PYTHONPATH=. uv run python agent_smoke_test_pydantic.py && uv run python -c "import pydantic_ai; print(pydantic_ai.__version__)"`
Expected: the wiring-smoke OK line + a `1.x` version. If any quoted behavior differs, fix the doc.
Also: `grep -nP "[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}]" docs/08-pydantic-ai-agent.md || echo "no emoji"` → `no emoji`. Then `uv sync` to restore base.

- [ ] **Step 3: Commit.**

```bash
git add docs/08-pydantic-ai-agent.md
git commit -m "docs: add PydanticAI agent comparison second-half lesson (08)"
```

---

## Task 7: Reframe `docs/00-overview.md` as two tracks

**Files:** Modify `docs/00-overview.md`.

- [ ] **Step 1: Read it:** `cat docs/00-overview.md`.

- [ ] **Step 2: Insert this section after the first intro paragraph (before the next `##`), verbatim:**

```markdown
## 兩軌:先手刻、再框架

這份教材分兩段:

- **前半段(`01`、`03`)** — 從零手刻 OpenAI tool-calling 迴圈,看懂 agent 怎麼讀 `tool_calls`、跑工具、把結果接回對話。
- **後半段(`08`)** — 用 **PydanticAI** agent 框架重寫同樣的 agent 當對照組,體會「框架把迴圈、工具 dispatch、schema 全包掉」,而工具邏輯(`run_tool`)兩版共用。

先手刻看懂 tool-loop,再用框架拿生產力 —— 你會清楚知道框架替你做了什麼、又沒替你做什麼(你的工具邏輯永遠是你自己的)。
```

- [ ] **Step 3:** If the file lists the doc series, add an entry for `08-pydantic-ai-agent.md` (`用 PydanticAI 重寫 agent 的對照組`) in the existing list's style. If no list, skip.

- [ ] **Step 4: Verify no emoji.**

Run: `grep -nP "[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}]" docs/00-overview.md || echo "no emoji"`
Expected: `no emoji`.

- [ ] **Step 5: Commit.**

```bash
git add docs/00-overview.md
git commit -m "docs: reframe overview as two tracks (hand-rolled + PydanticAI)"
```

---

## Task 8: Mirror Part 2 into `tutorial.html` + TOC

**Files:** Modify `tutorial.html`.

- [ ] **Step 1: Read it:** `cat tutorial.html` — study `<section>`/`<h2>`/`<h3>`/`<pre><code>`/`<table>` conventions, the header TOC (anchor links — note their exact href format: relative `docs/NN-...md` OR full `https://github.com/yazelin/telegram-ai-agent-starter/blob/main/docs/NN-...md`), and where `<main>` ends.

- [ ] **Step 2: Add an `08` TOC anchor** after the last TOC anchor (the `07-...` link), **matching the EXACT href format the sibling 00-07 anchors use** (if they use full GitHub blob URLs, use `https://github.com/yazelin/telegram-ai-agent-starter/blob/main/docs/08-pydantic-ai-agent.md`; if relative, use `docs/08-pydantic-ai-agent.md`). The link text is `08-pydantic-ai-agent`.

- [ ] **Step 3: Append a Part 2 `<section>`** inside `<main>` (after the last section, before `</main>`), mirroring `docs/08`. Use the file's element conventions. Include, matching docs/08 verbatim: the differences table (手刻 vs PydanticAI), `uv sync --extra pydantic`, the `@agent.tool_plain` add snippet, the `PYTHONPATH=. uv run python agent_smoke_test_pydantic.py` step + the deterministic-via-Test/FunctionModel note, the multiply bonus snippet, and the `AI_PROVIDER=pydantic` switch. No fabricated terminal output.

- [ ] **Step 4: Verify.**

Run:
```bash
uv run python -c "import html.parser; html.parser.HTMLParser().feed(open('tutorial.html').read()); print('html ok')"
grep -nP "[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}]" tutorial.html || echo "no emoji"
tail -c 40 tutorial.html
```
Expected: `html ok`, `no emoji`, ends with `</body></html>`. New `<section>` before `</main>`. TOC 08 anchor href format matches siblings.

- [ ] **Step 5: Commit.**

```bash
git add tutorial.html
git commit -m "docs: mirror PydanticAI Part 2 into tutorial.html + TOC"
```

---

## Task 9: Surface the two-track structure in README / index / DESIGN

**Files:** Modify `README.md`, `index.html`, `DESIGN.md`.

- [ ] **Step 1: Read all three** to find insertion points: `cat README.md DESIGN.md`; for index.html the features card.

- [ ] **Step 2: `README.md`** — add to the Features/功能 list (match existing bullet style):

```markdown
- PydanticAI agent 版同功能重寫(optional `pydantic` extra)— 見 `docs/08-pydantic-ai-agent.md`
```

After the existing quick-start / run instructions, add:

````markdown
### 後半段:PydanticAI agent 版(對照組)

```bash
uv sync --extra pydantic
PYTHONPATH=. uv run python agent_smoke_test_pydantic.py   # 框架接線 smoke(免 API key)
# .env 設 AI_PROVIDER=pydantic 後:
uv run uvicorn app.main:app                               # bot 改用 PydanticAI agent
```
````

If README has a docs/ link list, add `- 後半段(PydanticAI 對照組):docs/08-pydantic-ai-agent.md`.

- [ ] **Step 3: `DESIGN.md`** — in the 功能賣點/features list, add (match style):

```markdown
- 內建 PydanticAI agent 對照組(後半段 `docs/08`):同工具邏輯把手刻 tool-loop 用框架重寫,加工具一行 decorator
```

(If DESIGN.md already frames "agent 框架 / 進階" purely as a future direction that's now redundant, point it at the built-in docs/08 instead.)

- [ ] **Step 4: `index.html`** — in the features card `<ul>`, add one `<li>` matching sibling structure exactly:

```html
<li><span>後半段用 PydanticAI agent 框架重寫同功能(對照組),加工具一行 decorator</span></li>
```

- [ ] **Step 5: Verify.**

Run:
```bash
uv run python -c "import html.parser; html.parser.HTMLParser().feed(open('index.html').read()); print('index ok')"
test -f docs/08-pydantic-ai-agent.md && echo "link target exists"
grep -nP "[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}]" README.md DESIGN.md index.html || echo "no emoji"
```
Expected: `index ok`, `link target exists`, `no emoji`.

- [ ] **Step 6: Commit.**

```bash
git add README.md index.html DESIGN.md
git commit -m "docs: surface the PydanticAI second-half track in README/index/DESIGN"
```

---

## Final verification (after all tasks)

- [ ] **Both tracks green:**

```bash
uv sync && PYTHONPATH=. uv run python tools_smoke_test.py
uv sync --extra pydantic && PYTHONPATH=. uv run python agent_smoke_test_pydantic.py
uv sync
```
Expected: two `OK:` lines.

- [ ] **Base isolation:** `uv sync && PYTHONPATH=. uv run python -c "import app.agent; import importlib.util as u; print('pydantic_ai present:', u.find_spec('pydantic_ai') is not None)"` → `pydantic_ai present: False` and no import error.

- [ ] **No emoji drift:** `grep -rnP "[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}]" docs/ README.md DESIGN.md tutorial.html index.html || echo "clean"`.

---

## Self-review notes (author)

- **Spec coverage:** §4 two-track → Tasks 3/4/6/7; §3 verified facts → Tasks 1/3 (scratch-proven); §5 files → Tasks 1-9; framework wiring smoke via Test/FunctionModel (not end-to-end fake OpenAI) → Task 3; multiply bonus → Task 3 + docs; optional `pydantic` extra → Task 1; AI_PROVIDER=pydantic lazy branch → Task 4; CI matrix → Task 5; docs → Tasks 6-9.
- **Placeholder scan:** all code blocks complete and scratch-verified (slim[openai] imports, tool_plain wrappers over run_tool, Test/FunctionModel, OpenAIChatModel construction); doc tasks give exact insert blocks; tutorial/overview/README read the file first because they adapt to existing structure (incl. matching the TOC href format — a known gotcha from the company-ai repo), but the content to insert is fully specified.
- **Name consistency:** `agent` / `run_pydantic_agent` / `run_tool` / `run_http_agent` / tools `time`/`help`/`add`/`multiply` / env `AI_PROVIDER=pydantic` / extra `pydantic` / tests `tools_smoke_test.py`, `agent_smoke_test_pydantic.py` — consistent across tasks.
- **TOC gotcha:** Task 8 explicitly says match the sibling anchor href format (the company-ai tutorial used full GitHub blob URLs; verify this repo's format before adding the 08 anchor).
```
