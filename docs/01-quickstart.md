# Telegram AI Agent 入門模板：快速開始

這一頁帶你「不靠任何 token」就把程式跑起來、看到真實輸出，最後再說明需要 Telegram / LLM 金鑰才能做的那幾步（會明確標註）。

## 前置需求

- Python 3.10+（本文用 3.12.3 實測）
- Git
- 可以使用終端機
- 想接真實 Telegram / LLM 時，才需要對應帳號與 API key（後面標 **需金鑰** 的步驟）

## 第一步：安裝（不需任何 token）

```bash
git clone https://github.com/yazelin/telegram-ai-agent-starter.git
cd telegram-ai-agent-starter
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`pip install` 跑完最後一行會看到類似：

```
Successfully installed annotated-types-0.7.0 anyio-4.13.0 certifi-2026.5.20 click-8.4.1
fastapi-0.115.6 h11-0.16.0 httpcore-1.0.9 httptools-0.8.0 httpx-0.28.1 idna-3.17
pydantic-2.13.4 ... starlette-0.41.3 uvicorn-0.34.0 ...
```

成功的話你會看到：最後一行是 `Successfully installed ... fastapi-0.115.6 ... uvicorn-0.34.0 ...`，沒有紅色 ERROR。

## 第二步：啟動服務並做健康檢查（不需任何 token）

開一個終端機啟動 FastAPI：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

你會看到：

```
INFO:     Started server process [791496]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

另開一個終端機打健康檢查：

```bash
curl http://127.0.0.1:8000/health
```

真實輸出：

```
{"ok":true}
```

成功的話你會看到：`{"ok":true}`，而且第一個終端機多一行 `"GET /health HTTP/1.1" 200 OK`。這代表服務活著、`/health` 與 `/webhook/telegram` 兩個 endpoint 都已掛載。

## 第三步：用 echo provider 跑一次對話邏輯（不需任何 token）

`.env` 預設 `AI_PROVIDER=echo`，是純回聲、不需金鑰、適合第一次驗證。你不需要真的連 Telegram，可以直接在 Python 裡呼叫核心函式。

把下面存成 `/tmp/try_echo.py`（放在 repo 外，不要 commit）：

```python
import asyncio
from app.agent import ask_ai
from app.tools import run_tool

async def main():
    print("ask_ai echo:", repr(await ask_ai("hello from a learner")))
    print("run_tool time:", repr(await run_tool("time")))
    print("run_tool help:", repr(await run_tool("help")))

asyncio.run(main())
```

在 repo 根目錄跑（`AI_PROVIDER=echo` 是預設值，這裡顯式寫出來）：

```bash
AI_PROVIDER=echo python /tmp/try_echo.py
```

真實輸出：

```
ask_ai echo: 'Echo: hello from a learner'
run_tool time: '2026-06-02T03:30:19+08:00'
run_tool help: 'Try /ask your question or /tool time'
```

成功的話你會看到：echo provider 把你的句子加上 `Echo: ` 前綴回來，`time` 工具回一個 ISO 8601 時間字串。到這裡，「程式邏輯」已經完整跑通，完全不需要任何外部帳號。

> 注意：`echo` / `claude-cli` / `gemini-cli` 都是純對話，**不會**自動呼叫工具。只有 `http` provider 會做 tool-calling（見 `03-step-by-step.md`）。

## AI_PROVIDER 選項

`.env` 的 `AI_PROVIDER` 決定 `/ask` 怎麼回答，有效值：

- `echo`：純回聲，不需任何金鑰，適合離線 demo（**不會**呼叫工具）。
- `http`：OpenAI-compatible `/chat/completions` endpoint（OpenAI、本機 vLLM、Ollama 相容層等）。**唯一支援 tool-calling 的模式**：模型可自行決定呼叫 app/tools.py 裡的工具，結果會接回對話再產生最終答案。需設定 `HTTP_LLM_ENDPOINT`、`HTTP_LLM_API_KEY`、`MODEL_NAME`。
- `claude-cli`：呼叫本機 `claude -p`，純對話（**不會**自動呼叫工具）。
- `gemini-cli`：呼叫本機 `gemini -p`，純對話（**不會**自動呼叫工具）。

不論哪種模式，手動 `/tool time`、`/tool help` 指令都可用。

## 第四步：接真實 Telegram（**需金鑰**）

到這一步才需要 token。要讓 bot 真的在 Telegram 收發訊息：

1. **跟 BotFather 申請 bot**（**需金鑰**）：在 Telegram 搜尋 `@BotFather` → 傳 `/newbot` → 依指示取名 → 它會回給你一串 `TELEGRAM_BOT_TOKEN`（形如 `123456789:AAxxxxxxxx`）。
2. **取得你自己的 user id**：在 Telegram 搜尋 `@userinfobot`，傳任意訊息，它會回你的數字 id。
3. **填進 `.env`**：

   ```
   TELEGRAM_BOT_TOKEN=123456789:你的token
   ALLOWED_USER_IDS=你的user_id
   AI_PROVIDER=echo
   ```

   `ALLOWED_USER_IDS` 是 allow-list（白名單）：只有列在裡面的 user id 才能用這個 bot，其他人會收到 `Not allowed.`。多個 id 用逗號分隔。

4. **本機用 polling 模式啟動**（不需公開網址）：

   ```bash
   python -m app.polling
   ```

   設好 token 後，你在 Telegram 對你的 bot 傳 `/ask hello`，會看到它回 `Echo: hello`。
   （這一步需要真實 `TELEGRAM_BOT_TOKEN`，本文未實跑，故不貼造假輸出。）

## 第五步：部署後切換 webhook（**需金鑰 + 公開 HTTPS**）

webhook 模式需要一個對外的 HTTPS 網址。部署完之後告訴 Telegram 把 update 推到你的 endpoint，詳見 `04-deployment.md` 的 `setWebhook` 指令。

## 第一次成功的標準

- `pip install` 無 ERROR。
- `uvicorn` 啟動後 `curl /health` 回 `{"ok":true}`。
- echo driver 印出 `Echo: ...` 與 `time` 工具的時間字串。
- 你的 `TELEGRAM_BOT_TOKEN` 在 `.env` 裡、**沒有** commit 到 GitHub（`.gitignore` 已含 `.env`）。
