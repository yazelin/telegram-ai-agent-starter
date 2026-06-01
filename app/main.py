from fastapi import FastAPI, Request
from .telegram import handle_update
app=FastAPI(title="Telegram AI Agent Starter")
@app.get("/health")
def health(): return {"ok":True}
@app.post("/webhook/telegram")
async def webhook(request:Request):
    await handle_update(await request.json()); return {"ok":True}
