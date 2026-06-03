# Design: telegram Part 2 — PydanticAI agent 框架對照組

- **Date:** 2026-06-03
- **Repo:** `telegram-ai-agent-starter`
- **Status:** Approved design (pending written-spec review)

## 1. 目標與動機

前半段教學手刻了一個 OpenAI 相容的 **tool-calling 迴圈**(`app/agent.py:run_http_agent`):自己組 `messages`、`for _ in range(MAX_TOOL_ITERS)` 迴圈、手讀 `tool_calls`、手 dispatch `run_tool`、手接 `role:"tool"` 訊息。工具則是 `app/tools.py` 的 `TOOL_SCHEMAS`(手寫 JSON schema)+ `run_tool`(名稱 dispatch)**雙重維護**。

後半段新增一段**獨立課程**:用 **PydanticAI** agent 框架重寫同樣的 agent,讓學員看到「框架把迴圈、工具 dispatch、messages 管理、schema 自動生全包掉」。這是 mcp / linebot / company-ai 已驗證成功的「手刻 → 框架」教學模式套到 agent loop 場景。

非目標:不改 transport(polling/webhook 維持手刻);不動 echo / claude-cli / gemini-cli provider;不引 pytest。

## 2. 與前面 repo 的差異:agent loop 的「行為不確定」難題

mcp/linebot 用真傳輸+本地假 server 證明 parity;company-ai 用確定性 embedding 證對照。這裡的難點:**agent loop 要 LLM 決定呼叫哪個工具**,本質非確定。解法 — 用 **PydanticAI 內建的 `TestModel` / `FunctionModel`**(實測可行),不打真 LLM、免 API key、確定性地驅動 agent 並真的觸發工具。所以本軌走「**單元測工具 + 框架接線 smoke**」,不做端對端假 OpenAI(那是更重的做法,本案不需要)。

## 3. 已驗證的技術事實(實測)

- **pydantic-ai 1.105.0**;`Agent` + `@agent.tool_plain` 註冊工具。
- `TestModel()`:`agent.run_sync('hi', model=TestModel())` 自動以 dummy 參數呼叫**所有**註冊工具,回 JSON 摘要(實測 `{"add":"0.0","now":"TIME"}`)——證明工具被框架觸發,免 API key。
- `FunctionModel(fn)`:可腳本化「先回 `ToolCallPart(add, {a:19,b:23})` → 框架執行 add → 再回 `TextPart`」,實測最終 output = `The sum is 42.0`,add 確實被執行。
- 完整 `pydantic-ai` 會拉 147 個套件(含 botocore/temporalio/mistralai/grpcio 等)→ 太肥;改用 **`pydantic-ai-slim[openai]`**(只帶 OpenAI provider;`TestModel`/`FunctionModel` 在 slim core)。實際 import 面與 slim 是否含 Test/FunctionModel + OpenAIModel,於 writing-plans 前 scratch 再確認;smoke test 為最終防線。

## 4. 架構(兩軌 + 共用工具邏輯)

| | Part 1（現有） | Part 2（新增） |
|---|---|---|
| tool-loop | 手刻 `for _ in range(MAX_TOOL_ITERS)` + 手接 `role:tool` | 框架擁有迴圈 |
| 工具註冊 | `TOOL_SCHEMAS`(手寫 JSON)+ `run_tool`(dispatch)雙重維護 | `@agent.tool_plain` 一個 decorator;schema 由型別自動生 |
| 工具邏輯 | `run_tool` | **共用**:框架工具是薄 typed wrapper 呼叫 `run_tool`(DRY、行為一致) |
| 相依 | base（無 agent 框架） | pydantic-ai-slim[openai]（optional `pydantic` extra） |
| 切換 | `AI_PROVIDER` | `AI_PROVIDER=pydantic` 讓 `ask_ai` 走框架版 |

**被框架移除的是「手寫 schema + 手刻迴圈」,不是工具邏輯**:framework 的 `add` 等 decorated 工具呼叫既有 `run_tool`,所以兩版行為必然一致,且不重複工具邏輯。

## 5. 檔案清單

### 程式碼
- **`app/agent_pydantic.py`(新)**:
  - 建 `Agent`(system prompt);`@agent.tool_plain` 註冊 `time` / `help` / `add`,每個是 typed wrapper 呼叫 `from .tools import run_tool`。
  - `run_pydantic_agent(message) -> str`:用 `OpenAIModel`(base_url 由 `HTTP_LLM_ENDPOINT` 推導、api_key 由 `HTTP_LLM_API_KEY`)`await agent.run(message)` 回 `.output`。lazy 載入框架。
  - 紅利:多一個 `multiply` 工具(一個 decorator,自帶 body),示範「加工具一行」。
- **`app/agent.py`(改)**:`ask_ai` 加 `if config.AI_PROVIDER == "pydantic": from .agent_pydantic import run_pydantic_agent; return await run_pydantic_agent(message)`(lazy import,base 匯入鏈不碰框架)。
- **`pyproject.toml`(改)**:`[project.optional-dependencies] pydantic = ["pydantic-ai-slim[openai]>=1,<2"]`;`[tool.uv] package = false` 不變。
- **`uv.lock`（重產）**。

### 測試 / CI
- **`tools_smoke_test.py`(新,base)**:單元測 `run_tool`:`time` 回 ISO-ish、`help` 回提示、`add({a:19,b:23})` → `"42.0"`、unknown → `Unknown tool: ...`。
- **`agent_smoke_test_pydantic.py`(新,pydantic extra)**:
  - `FunctionModel` 腳本叫 `add(19,23)` → 斷言 agent 觸發 add、最終 output 反映之。
  - `TestModel` → 斷言 `time`/`help`/`add` 三工具都註冊且被叫。
  - 紅利:`FunctionModel` 腳本叫 `multiply(6,7)` → 斷言 `"42.0"` 且 multiply 有註冊。
- **`.github/workflows/ci.yml`(新)**:matrix:`base`(base 相依,跑 tools smoke)/ `pydantic`(`uv sync --extra pydantic`,跑 agent smoke)。

### 文件
- **`docs/08-pydantic-ai-agent.md`(新)**:手刻 loop vs 框架差異表、裝 extra、`@agent.tool_plain` 對照 `TOOL_SCHEMAS`+`run_tool`、用 Test/FunctionModel 跑確定性 smoke、加工具一行紅利、何時用框架、`AI_PROVIDER=pydantic` 切換。
- **`docs/00-overview.md`、`tutorial.html`(含 TOC 補 08)、`README.md`、`index.html`、`DESIGN.md`(改)**:兩軌化;agent 框架從「可延伸」升格為「內建後半段」。

## 6. 錯誤處理 / 邊界

- `agent_pydantic.py` 在無 pydantic-ai(沒裝 extra)時匯入即失敗 —— 預期(僅 `AI_PROVIDER=pydantic` 或 pydantic track 才匯入)。
- 測試用 `TestModel`/`FunctionModel`,不需要真 LLM endpoint 或 key。
- `run_pydantic_agent` 真跑時的 base_url:`HTTP_LLM_ENDPOINT` 在現有 repo 是完整 `.../v1/chat/completions`;PydanticAI 的 OpenAI provider 要 base(`.../v1`)。plan 會處理(推導 base 或文件註明),且測試不依賴它。

## 7. 風險與待確認

- **pydantic-ai-slim[openai] 是否含 TestModel/FunctionModel/OpenAIModel + 安裝面是否夠輕**:writing-plans 前 scratch 確認;smoke test 為防線。
- **real endpoint base_url 接法**:plan scratch 驗;測試不依賴。
- **版本飄移**:鎖 `>=1,<2`;Test/FunctionModel 為確定性防線;docs 標版本(1.105.x)。
- **base 隔離**:框架只在 `agent_pydantic.py` 頂部與 `ask_ai` 的 pydantic 分支 import;`AI_PROVIDER` 預設不觸發,確保 base `uv sync` 不裝框架、手刻版可獨立跑。

## 8. 不做（YAGNI）

- transport 軸(raw polling/webhook → python-telegram-bot/aiogram)不做(弱對照)。
- 不端對端假 OpenAI(用框架內建 Test/FunctionModel 即足夠且更輕)。
- 不引 pytest。
- 不動 `run_http_agent` 手刻版(保留為對照基準)、不動 echo/claude-cli/gemini-cli。
