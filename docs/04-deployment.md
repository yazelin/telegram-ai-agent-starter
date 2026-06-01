# Telegram AI Agent 入門模板：部署筆記

## 部署前檢查

- 本機流程已經跑通。
- `.env` 沒有被 commit。
- README 的啟動指令與實際程式一致。
- `/health` 或等價檢查 endpoint 可用。
- 外部服務 token 已放在部署平台 secrets。

## 啟動指令

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 設定 webhook

部署到有公開 HTTPS 網址後，告訴 Telegram 把 update 推到你的 `/webhook/telegram`：

```bash
curl -F "url=https://YOUR_DOMAIN/webhook/telegram" \
  "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook"
```

回傳 `{"ok":true,...}` 即設定成功。要清掉改回本機開發時用 polling，可呼叫 `deleteWebhook`：

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook"
```

## Webhook vs Polling

- **Webhook（正式部署）**：Telegram 主動把 update POST 到 `/webhook/telegram`（app/main.py）。需要公開 HTTPS 網址，省資源、低延遲。設定完 webhook 後 **不要**同時跑 polling，否則會搶 update。
- **Polling（本機開發）**：`python -m app.polling` 用 getUpdates + offset 主動拉，不需公開網址，適合本機 debug。切到 polling 前記得先 `deleteWebhook`。

## 常見部署選項

- Render / Railway / Fly.io：適合快速 demo。
- VPS + Docker / systemd：適合長期自管。
- 公司內網主機：適合企業內部工具，但要處理網路與權限。
- NAS / edge gateway：適合工業或內部自動化場景。

## 部署後驗證

```bash
curl http://127.0.0.1:8000/health
```

接著再測真正的業務流程，不要只看服務有沒有啟動。

## 實務提醒

部署不是最後一步。正式使用前至少要補：log、錯誤告警、權限控管、備份策略、secret rotation，以及基本監控。
