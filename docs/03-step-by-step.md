# Telegram AI Agent 入門模板：完整操作流程

## 步驟

1. 先用 AI_PROVIDER=echo 確認 Telegram 收發訊息正常。
2. 確認自己的 Telegram user id 已放進 ALLOWED_USER_IDS。
3. 用 python -m app.polling 測本機互動，避免一開始處理 webhook HTTPS 問題。
4. 改成 claude-cli、gemini-cli 或 http provider。
5. 部署後把公開網址設定成 Telegram webhook。
6. 把常用腳本或 API 包進 app/tools.py，變成自己的工作流助理。

## 建議紀錄

- 你使用的 Python 版本
- 啟動指令
- `.env` 裡有哪些 key 已設定；不要貼出 secret 值
- webhook / endpoint URL
- 錯誤訊息完整內容
- 你預期發生什麼、實際發生什麼

## 下一個里程碑

完成最小流程後，不要急著加功能。先找一個真實情境，讓這個 starter 解決一個很小但明確的問題。
