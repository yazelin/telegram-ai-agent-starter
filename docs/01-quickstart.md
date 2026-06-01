# Telegram AI Agent 入門模板：快速開始

## 前置需求

- Python 3.10+
- Git
- 可以使用終端機
- 如果要接真實 AI 或平台 token，請準備對應帳號與 API key。

## 最短路徑

1. 建立 Telegram bot 並取得 TELEGRAM_BOT_TOKEN
2. 設定 ALLOWED_USER_IDS 避免陌生人亂用
3. 本機用 polling 模式開發
4. 部署後切換 webhook 模式

## 安裝與啟動

```bash
git clone https://github.com/yazelin/telegram-ai-agent-starter.git
cd telegram-ai-agent-starter
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env：TELEGRAM_BOT_TOKEN、ALLOWED_USER_IDS、AI_PROVIDER
python -m app.polling
```

## 健康檢查

```bash
curl http://127.0.0.1:8000/health
```

## 常用入口

- GET /health：健康檢查
- POST /webhook/telegram：Telegram webhook 收 update

## 第一次成功的標準

- 服務能啟動
- 基本 endpoint 有回應
- 範例流程能跑通
- 秘密 token 沒有 commit 到 GitHub
