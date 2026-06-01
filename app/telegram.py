import httpx
from .config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
from .agent import ask_ai
from .tools import run_tool
API=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
async def handle_update(update):
    msg=update.get("message") or {}; text=msg.get("text",""); chat_id=msg.get("chat",{}).get("id"); user_id=msg.get("from",{}).get("id")
    if not chat_id or not text: return
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS: return await send_message(chat_id,"Not allowed.")
    if text.startswith("/start"): reply="Hi! Use /ask or /tool time."
    elif text.startswith("/tool"):
        parts=text.split(maxsplit=2)  # ["/tool", NAME, REST...]
        name=parts[1] if len(parts)>1 else "help"
        arguments={"input":parts[2]} if len(parts)>2 else {}
        reply=await run_tool(name, arguments)
    else: reply=await ask_ai(text.removeprefix("/ask").strip())
    await send_message(chat_id, reply[:3900])
async def send_message(chat_id,text):
    async with httpx.AsyncClient(timeout=30) as c: await c.post(API+"/sendMessage",json={"chat_id":chat_id,"text":text})
