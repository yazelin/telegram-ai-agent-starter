![Brand banner](assets/banner.svg)

# Telegram AI Agent Starter

Build a Telegram AI assistant that can call LLMs and tools.

## 繁中定位

**Telegram AI Agent 入門模板** 面向台灣繁中受眾。

- 主要受眾：適合想把 Telegram 變成 AI 工作入口的台灣工程師、接案者與小團隊。
- 核心承諾：從一個 bot token 開始，做出會回覆、會呼叫工具、可部署的 AI Agent。
- CTA 頁：https://yazelin.github.io/telegram-ai-agent-starter/



## 公開教學文件

這個 repo 的教學內容直接公開，讓你可以先自己照著跑；如果需要手把手 debug、改成你的公司或個人場景，再考慮工作坊或顧問協助。

- 網頁版教學：https://yazelin.github.io/telegram-ai-agent-starter/tutorial.html
- Markdown 教學：[`docs/`](docs/)
- 快速開始：[`docs/01-quickstart.md`](docs/01-quickstart.md)
- 常見踩雷：[`docs/05-common-pitfalls.md`](docs/05-common-pitfalls.md)

## Who this is for

Engineers who want a deployable Telegram AI workflow bot.

## Features

- FastAPI webhook + polling dev mode
- Echo / Claude CLI / Gemini CLI / HTTP provider adapters
- Allow-list user IDs and simple tool router
- Docker-ready starter for workshops

## Quick start

```bash
git clone https://github.com/yazelin/telegram-ai-agent-starter.git
cd telegram-ai-agent-starter
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # if present
```

See the source files and `.env.example` for the minimal runnable path.

## Learn / get help

This repo is also a CTA page for workshops and consulting:

- GitHub Pages: https://yazelin.github.io/telegram-ai-agent-starter/
- Contact: yaze.lin.j303@gmail.com

## License

MIT


## Brand / CTA design

- Landing page: https://yazelin.github.io/telegram-ai-agent-starter/
- CI spec: [DESIGN.md](DESIGN.md)
- Banner: [assets/banner.svg](assets/banner.svg)
- Logo: [assets/logo.svg](assets/logo.svg)
