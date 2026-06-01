# Telegram AI Agent 入門模板：常見問題與踩雷清單

## 常見坑

- Bot token 不要 commit 到 GitHub，永遠放 .env 或部署平台 secrets。
- ALLOWED_USER_IDS 空白代表不限制使用者，公開部署前一定要確認。
- Telegram webhook 需要 HTTPS，本機測試建議先用 polling。
- LLM 回覆可能超過 Telegram 長度限制，程式已截斷到約 3900 字，但實務上仍建議摘要。
- claude-cli / gemini-cli 要先在伺服器上登入與測試。

## Debug 順序

1. 先確認服務有沒有啟動。
2. 再確認 endpoint / webhook URL 是否正確。
3. 檢查環境變數是否有載入。
4. 用 echo / fake provider 排除 AI 服務問題。
5. 查看完整錯誤訊息，不要只看最後一行。
6. 把問題縮到最小可重現案例。

## 問別人前準備

- repo / branch
- 啟動指令
- 完整錯誤訊息
- 你已經檢查過哪些設定
- secret 請遮掉，不要直接貼 token
