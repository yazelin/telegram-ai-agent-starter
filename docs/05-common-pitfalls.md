# Telegram AI Agent 入門模板：常見問題與踩雷清單

這裡每一條都附「真實 / 預期的症狀」，方便你對照自己遇到的狀況。

## 1. 不在 ALLOWED_USER_IDS → 收到 `Not allowed.`

`ALLOWED_USER_IDS` 是 allow-list。只要它非空，沒列進去的 user id 一律被擋。實測（用 driver 模擬一個 allowed user 和一個非 allowed user）：

```
-> chat 500: 'Echo: what time is it'      # user 在白名單，正常回覆
-> chat 500: '2026-06-02T03:30:27+08:00'  # /tool time 正常
-> chat 999: 'Not allowed.'               # user 不在白名單，被擋
```

- 症狀：你或別人傳訊息，bot 只回 `Not allowed.`。
- 原因：該 user id 不在 `ALLOWED_USER_IDS`。
- 修法：用 `@userinfobot` 查到正確的數字 id，加進 `.env` 的 `ALLOWED_USER_IDS`（逗號分隔），重啟。
- 反向陷阱：`ALLOWED_USER_IDS` **留空代表不限制任何人**。公開部署前一定要填，否則陌生人都能用你的 bot 和你的 LLM 額度。

## 2. polling 遇到壞回應 → 已容錯，不會崩

早期版本 `getUpdates` 一遇到 429 或非 JSON 的 body 就整個 crash。現在 `app/polling.py` 會退避重試。實測（餵它一個 429 再餵一個非 JSON body）：

```
[server returned] HTTP 429 (rate limited)
[server returned] HTTP 200 with non-JSON body '<html>not json</html>'
[polling] getUpdates failed: JSONDecodeError('Expecting value: line 1 column 1 (char 0)'); retrying...
[demo result] loop survived both bad responses and kept polling
```

- 症狀：偶發 `[polling] getUpdates failed: ...; retrying...`，但程式沒死、過幾秒自己恢復。
- 原因：Telegram 限流（429）或回了非預期內容（5xx HTML）。
- 處理：這是正常的退避重試，不用管。若**一直**重試，去查 `TELEGRAM_BOT_TOKEN` 是否正確、網路是否能連到 `api.telegram.org`。

## 3. webhook 沒回應 → 多半是不是 HTTPS / 沒設對

- 症狀：訊息傳進去 bot 沒反應，但 polling 模式是好的。
- 原因：Telegram webhook **只接受公開 HTTPS 網址**；`http://` 或內網位址不行。
- 修法：先確認 `setWebhook` 回 `{"ok":true}`（見 `04-deployment.md`）；用 `curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo` 看 `last_error_message`。
- 常見衝突：**同時跑 webhook 和 polling 會互搶 update**。切回 polling 前先 `deleteWebhook`。

## 4. 選錯 provider → agent 不會呼叫工具

- 症狀：你期待 bot「自己去查時間 / 算數」，但它只回一句閒聊，工具從沒被呼叫。
- 原因：`echo` / `claude-cli` / `gemini-cli` 都是純對話，**不送 `tools=`**。只有 `http` 會做 tool-calling。
- 修法：把 `.env` 改成 `AI_PROVIDER=http`，並設好 `HTTP_LLM_ENDPOINT` / `HTTP_LLM_API_KEY` / `MODEL_NAME`。驗證方式見 `03-step-by-step.md` 的模擬。
- 延伸：加了新工具卻沒被呼叫？檢查 schema 的 `name` 和 `run_tool` 的分支是否完全一致，不一致會掉進 `Unknown tool:`。

## 5. token 外洩 / 沒載入

- 不要 commit `TELEGRAM_BOT_TOKEN`。`.gitignore` 已含 `.env`，把 secret 放那裡或放部署平台 secrets。
- 環境變數沒載入時，`config.TELEGRAM_BOT_TOKEN` 會是空字串，呼叫 Telegram API 會 401。先確認 `.env` 在 repo 根目錄、`python-dotenv` 有讀到。

## 6. 回覆太長被 Telegram 截斷

LLM 可能回超過 Telegram 單則訊息上限的內容。程式已截到約 3900 字（`reply[:3900]`），但實務上建議在工具 / prompt 端就做摘要，而不是硬截。

## 7. uv 沒裝 / 忘了 uv sync → 指令找不到或 ImportError

- 症狀：`uv: command not found`，或 `uv run` 報 `ModuleNotFoundError: No module named 'fastapi'`。
- 原因：沒裝 uv，或 clone 後還沒跑 `uv sync` 建好 `.venv`。
- 修法：先依 `01-quickstart.md` 裝 uv（Ubuntu/macOS 用 `curl -LsSf https://astral.sh/uv/install.sh | sh`，Windows 用 PowerShell 那條），裝完重開終端機確認 `uv --version`；再在 repo 根目錄跑一次 `uv sync`。之後所有指令都用 `uv run ...` 開頭，毋須手動 venv/activate。
- 延伸：直接打 `uvicorn ...` / `python -m app.polling`（沒有 `uv run` 前綴）會用到系統 Python 而非專案 `.venv`，常見就是這樣噴 ImportError。

## Debug 順序

1. 服務有沒有啟動（`curl /health` 是否回 `{"ok":true}`）。
2. endpoint / webhook URL 是否正確（`getWebhookInfo`）。
3. 環境變數是否載入。
4. 用 `echo` provider 排除 LLM 那一側的問題。
5. 看完整錯誤訊息，不要只看最後一行。
6. 縮到最小可重現案例（像本頁那樣用一支小 driver 重現）。

## 問別人前準備

- repo / branch、啟動指令
- 完整錯誤訊息（secret 遮掉，不要貼 token）
- 你已經檢查過哪些設定、預期 vs 實際
