# Telegram AI Agent 入門模板 CI Design

> English name: Telegram AI Agent Starter

## 定位

**主要受眾：** 適合想把 Telegram 變成 AI 工作入口的台灣工程師、接案者與小團隊。  
**核心承諾：** 從一個 bot token 開始，做出會回覆、會呼叫工具、可部署的 AI Agent。  
**痛點切入：** 不用先研究一堆框架，先把「能跑、能部署、能接工具」的最小版本做出來。  
**類別提示：** Telegram webhook / polling / tools

## 視覺識別

- **主色：** `#38bdf8`
- **輔色：** `#2563eb`
- **背景：** `#06111f`
- **語言策略：** 繁體中文為主，英文產品名作為輔助與 SEO。
- **風格：** dark developer-tool landing page、技術網格、明確產品 glyph、高對比 CTA。

## Landing Page CTA

主要 CTA：**取得 Telegram AI Agent 教學筆記**  
表單會帶上 repo 名稱 `telegram-ai-agent-starter` 與語言 `zh-Hant-TW`，方便後續分眾。

## 功能賣點

- Webhook + polling 雙模式，開發與部署都能用
- echo / Claude CLI / Gemini CLI / HTTP provider adapter
- HTTP（OpenAI-compatible）模式內建 function-calling 迴圈：agent 會自己呼叫工具並把結果接回對話；其他 provider 為純 chat
- Telegram 使用者 allow-list，避免陌生人亂用
- 內建 /ask 與手動 /tool 範例，適合延伸成個人助理

## Assets

- `assets/banner.svg`：README / Open Graph / hero banner
- `assets/logo.svg`：square product mark
- `index.html`：繁中 GitHub Pages CTA landing page
