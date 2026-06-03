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
