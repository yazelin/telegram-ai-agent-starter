# Telegram AI Agent 入門模板：總覽

從一個 bot token 開始，做出會回覆、會呼叫工具、可部署的 AI Agent。

## 兩軌:先手刻、再框架

這份教材分兩段:

- **前半段(`01`、`03`)** — 從零手刻 OpenAI tool-calling 迴圈,看懂 agent 怎麼讀 `tool_calls`、跑工具、把結果接回對話。
- **後半段(`08`)** — 用 **PydanticAI** agent 框架重寫同樣的 agent 當對照組,體會「框架把迴圈、工具 dispatch、schema 全包掉」,而工具邏輯(`run_tool`)兩版共用。

先手刻看懂 tool-loop,再用框架拿生產力 —— 你會清楚知道框架替你做了什麼、又沒替你做什麼(你的工具邏輯永遠是你自己的)。

## 適合誰

想把 Telegram 變成 AI 工作入口的台灣工程師、接案者與小團隊。

## 你會做出什麼

- 個人 AI 工作助理
- 團隊內部通知與問答入口
- 接 Claude CLI / Gemini CLI 的輕量 bot
- 把常用工具包成 /tool 指令

## 建議學習方式

1. 先照 `01-quickstart.md` 跑起來。
2. 再看 `02-architecture.md` 理解每個檔案負責什麼。
3. 照 `03-step-by-step.md` 做一次完整流程。
4. 準備部署時看 `04-deployment.md`。
5. 卡住時先查 `05-common-pitfalls.md`。
6. 想改成自己的場景，看 `06-customize-for-your-use-case.md`。
7. 後半段對照組:看 `08-pydantic-ai-agent.md`(用 PydanticAI 重寫 agent 的對照組)。

## 免費與付費怎麼分

這個 repo 會公開最小可跑版本與完整操作步驟。真正適合工作坊或顧問的部分，是陪你 debug、改成你的情境、處理部署與實務安全邊界。

- 免費：可重現的 starter、教學文件、基本部署方向。
- 付費工作坊：手把手解問題、看你的程式與設定、一起改成你的使用場景。
- 企業顧問：需求訪談、PoC、部署、權限、安全與維運規劃。
