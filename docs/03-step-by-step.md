# Telegram AI Agent 入門模板：帶你走一遍

這一頁不只列步驟，而是帶你把「一個會自己呼叫工具的 agent」實際跑出來看到。最重要的是中段那一節：用本機模擬完整重現 tool-calling 迴圈，你會看清楚「LLM 決定呼叫工具 → 工具真的執行 → 結果接回去 → 模型給最終答案」每一格。

## 大流程

1. 先用 `AI_PROVIDER=echo` 確認對話邏輯正常（見 `01-quickstart.md` 第三步，已實測 `Echo: ...`）。
2. 確認自己的 Telegram user id 已放進 `ALLOWED_USER_IDS`（allow-list）。
3. 用 `python -m app.polling` 測本機互動，避免一開始就處理 webhook HTTPS。
4. 想要 agent 自己呼叫工具時，改用 `http` provider（本頁重點）。
5. 部署後把公開網址設成 Telegram webhook（見 `04-deployment.md`）。
6. 把你常用的腳本 / API 包進 `app/tools.py`，變成自己的工作流助理。

## 哪種 provider 會呼叫工具？

| AI_PROVIDER | 行為 | 自動呼叫工具 |
| --- | --- | --- |
| `echo` | 純回聲 | 否 |
| `claude-cli` | 本機 `claude -p` 純對話 | 否 |
| `gemini-cli` | 本機 `gemini -p` 純對話 | 否 |
| `http` | OpenAI-compatible `/chat/completions` | **是** |

只有 `http` 會把 `tools=TOOL_SCHEMAS` 一起送出去，讓模型自行決定要不要呼叫工具。以下示範就是針對 `http`。

## 重點：完整看一次 tool-calling 迴圈（本機模擬）

接真實 OpenAI / vLLM 要花錢、要金鑰，而且每次回應不固定，不適合教學。我們改用**本機模擬**：用一個假的 `httpx.AsyncClient` 取代真網路，讓它第一次回「我要呼叫 `time` 工具」、第二次回最終答案。`app/agent.py` 裡那段真正的迴圈邏輯**完全沒有改動**，所以你看到的執行路徑就是真實的那一條。

> 以下標記為**本機模擬，非真實外部 LLM 回應**：模型回什麼是我們腳本指定的，但「送出去的內容、工具的執行、結果如何接回」全是程式真的跑出來的。

把下面存成 `/tmp/mock_toolloop.py`（放在 repo 外）：

```python
import asyncio
import app.config as config
config.AI_PROVIDER = "http"
config.HTTP_LLM_ENDPOINT = "https://mock.local/v1/chat/completions"
config.HTTP_LLM_API_KEY = ""
config.MODEL_NAME = "mock-model"

import app.agent as agent

# 重播佇列：第 1 次回應請求呼叫 time 工具，第 2 次給最終文字。
RESPONSES = [
    {"choices": [{"message": {
        "role": "assistant", "content": None,
        "tool_calls": [{"id": "call_001", "type": "function",
            "function": {"name": "time", "arguments": "{}"}}]}}]},
    {"choices": [{"message": {
        "role": "assistant",
        "content": "現在時間是 2026-06-02T03:30（由 time 工具取得）。"}}]},
]

class MockResponse:
    def __init__(self, data): self._data = data
    def raise_for_status(self): pass
    def json(self): return self._data

class MockAsyncClient:        # 取代真實的 httpx.AsyncClient
    def __init__(self, *a, **k): self._i = 0
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def post(self, url, json=None, headers=None):
        print(f"--- HTTP POST #{self._i+1} -> {url}")
        print("    messages sent:")
        for m in json["messages"]:
            print("      ", m)
        print("    tools= sent:", "yes (" + ", ".join(
            t['function']['name'] for t in json['tools']) + ")"
            if "tools" in json else "no (final plain call)")
        resp = RESPONSES[self._i]; self._i += 1
        return MockResponse(resp)

agent.httpx.AsyncClient = MockAsyncClient

# 包一層 run_tool 讓你看到工具真的被執行。
orig_run_tool = agent.run_tool
async def traced_run_tool(name, arguments):
    result = await orig_run_tool(name, arguments)
    print(f"    >>> run_tool({name!r}, {arguments!r}) executed -> {result!r}")
    return result
agent.run_tool = traced_run_tool

async def main():
    final = await agent.ask_ai("現在幾點？")
    print("=== FINAL ANSWER ===")
    print(final)

asyncio.run(main())
```

在 repo 根目錄跑：

```bash
PYTHONPATH=. python /tmp/mock_toolloop.py
```

真實輸出（**本機模擬，非真實外部 LLM 回應**）：

```
--- HTTP POST #1 -> https://mock.local/v1/chat/completions
    messages sent:
       {'role': 'user', 'content': '現在幾點？'}
    tools= sent: yes (time, help)
    >>> run_tool('time', {}) executed -> '2026-06-02T03:30:53+08:00'
--- HTTP POST #2 -> https://mock.local/v1/chat/completions
    messages sent:
       {'role': 'user', 'content': '現在幾點？'}
       {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'call_001', 'type': 'function', 'function': {'name': 'time', 'arguments': '{}'}}]}
       {'role': 'tool', 'tool_call_id': 'call_001', 'name': 'time', 'content': '2026-06-02T03:30:53+08:00'}
    tools= sent: yes (time, help)
=== FINAL ANSWER ===
現在時間是 2026-06-02T03:30（由 time 工具取得）。
```

逐格看懂這個迴圈（對照 `app/agent.py` 的 `run_http_agent`）：

1. **第 1 次 POST**：只送使用者問題，但帶上 `tools=`（`time`, `help`）。模型回的不是文字，而是 `tool_calls`，指名要呼叫 `time`。
2. **工具真的執行**：程式解析 `tool_call`，用 `run_tool("time", {})` 跑出 `2026-06-02T03:30:53+08:00`。
3. **結果接回對話**：把模型那一輪 assistant 訊息、加上一則 `role:"tool"`（帶相同的 `tool_call_id`）一起塞回 `messages`。
4. **第 2 次 POST**：帶著「工具結果」再問一次，這次模型回最終文字。迴圈結束（最多 `MAX_TOOL_ITERS = 4` 次）。

這就是「agent 會自己呼叫工具」的本體：模型決定、程式執行、結果回灌、模型總結。

## 動手練習：自己加一個工具，讓 agent 會呼叫它

目標：新增一個 `add(a, b)` 加法工具，並用同一套模擬證明 agent 真的會呼叫它。這是真的要動手、而且本文已經實跑驗證過的練習。

### before：`app/tools.py` 只有 time / help

`TOOL_SCHEMAS` 原本只有兩個工具，`run_tool` 也只 dispatch 這兩個。

### after：加上 add

在 `TOOL_SCHEMAS` 末尾加一個 schema（注意要描述參數 `a`, `b`）：

```python
{
    "type": "function",
    "function": {
        "name": "add",
        "description": "Add two numbers and return the sum.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First addend."},
                "b": {"type": "number", "description": "Second addend."},
            },
            "required": ["a", "b"],
        },
    },
},
```

並在 `run_tool` 加一條 dispatch 分支：

```python
if name == "add":
    try:
        return str(float(arguments["a"]) + float(arguments["b"]))
    except (KeyError, TypeError, ValueError):
        return "add needs numeric arguments a and b"
```

### 先單獨驗證工具本身（不需金鑰）

```bash
PYTHONPATH=. python -c "
import asyncio
from app.tools import run_tool
async def main():
    print('direct add:', repr(await run_tool('add', {'a': 19, 'b': 23})))
    print('add missing:', repr(await run_tool('add', {})))
asyncio.run(main())
"
```

真實輸出：

```
direct add: '42.0'
add missing: 'add needs numeric arguments a and b'
```

### 再證明 agent 會自己呼叫 add（本機模擬）

複製上面那支 `mock_toolloop.py`，把 `RESPONSES` 改成讓模型要求呼叫 `add`：

```python
RESPONSES = [
    {"choices": [{"message": {"role": "assistant", "content": None,
        "tool_calls": [{"id": "call_add_1", "type": "function",
            "function": {"name": "add", "arguments": '{"a": 19, "b": 23}'}}]}}]},
    {"choices": [{"message": {"role": "assistant",
        "content": "19 加 23 等於 42（由 add 工具計算）。"}}]},
]
```

跑出來的真實輸出（**本機模擬，非真實外部 LLM 回應**）：

```
Tools now exposed to the model: ['time', 'help', 'add']
--- HTTP POST #1
       {'role': 'user', 'content': '19 加 23 是多少？'}
    >>> run_tool('add', {'a': 19, 'b': 23}) -> '42.0'
--- HTTP POST #2
       {'role': 'user', 'content': '19 加 23 是多少？'}
       {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'call_add_1', 'type': 'function', 'function': {'name': 'add', 'arguments': '{"a": 19, "b": 23}'}}]}
       {'role': 'tool', 'tool_call_id': 'call_add_1', 'name': 'add', 'content': '42.0'}
19 加 23 等於 42（由 add 工具計算）。
```

重點觀察：

- 第一行 `Tools now exposed to the model: ['time', 'help', 'add']` 證明新工具已經被送進 `tools=`，模型「看得到」它。
- 模型要求 `add(a=19, b=23)`，`run_tool` 真的算出 `42.0`，再以 `role:"tool"` 接回，模型才給最終答案。

這就是加工具的完整套路：**schema 進 `TOOL_SCHEMAS` + dispatch 進 `run_tool`**，兩處對齊 `name` 即可。把 `add` 換成「查庫存」「叫 AGV」「打公司 API」，邏輯一模一樣。

> 真實接 OpenAI 等模型時（**需金鑰**），是否呼叫工具、呼叫哪一個由模型自己判斷；上面的模擬只是把那個決定固定下來，方便你看清執行路徑。

## 提醒

- `/tool add ...` 這種**手動**指令目前只會把參數打包成 `{"input": ...}`，不會自動拆成 `a` / `b`。手動指令適合 `time` / `help` 這類無參數工具；要餵 `a` / `b`，走 `http` provider 讓模型產生 JSON arguments 才自然。
- 加完工具記得：`name` 在 schema 和 `run_tool` 要一致，否則模型呼叫時會落到 `Unknown tool:`。
