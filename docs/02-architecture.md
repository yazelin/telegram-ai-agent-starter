# Telegram AI Agent 入門模板：架構說明

## 核心檔案

- app/main.py：FastAPI webhook 入口
- app/polling.py：本機開發用 getUpdates polling
- app/telegram.py：解析 Telegram update、權限檢查、送訊息
- app/agent.py：AI provider adapter，支援 echo / claude-cli / gemini-cli / http；`http` 模式內建 OpenAI-compatible function-calling 迴圈
- app/tools.py：`TOOL_SCHEMAS`（OpenAI 工具 schema）與 `run_tool(name, arguments)` dispatch，目前提供 `time` / `help`

## 資料流

1. Telegram 把訊息送進來，有兩種入口：
   - Webhook：`POST /webhook/telegram`（app/main.py，FastAPI）
   - Long-poll：`python -m app.polling` 用 getUpdates + offset 拉更新（本機開發用）
2. `handle_update`（app/telegram.py）解析 update、做 allow-list 權限檢查。
3. 指令分流：`/tool NAME` 直接呼叫 `run_tool`；其餘文字交給 `ask_ai`。
4. `ask_ai`（app/agent.py）依 `AI_PROVIDER` 路由；`http` 模式會把對話加上 `tools=TOOL_SCHEMAS` 送到 `/chat/completions`，若回傳 `tool_calls` 就執行對應工具、把結果以 `role:"tool"` 訊息接回去，最多迴圈 4 次直到模型給出最終文字。
5. 用 sendMessage 把回覆送回 Telegram。

## 設計原則

- 先讓流程可跑，再做漂亮抽象。
- token 與 secrets 全部放在環境變數。
- 每一層保持可以替換：入口、AI provider、資料來源、部署方式。
- 範例程式刻意保持小，方便你看懂後改成自己的版本。
