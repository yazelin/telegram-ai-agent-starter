import asyncio, httpx
from .config import TELEGRAM_BOT_TOKEN
from .telegram import handle_update
API=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
async def main():
    offset=0
    async with httpx.AsyncClient(timeout=60) as c:
        while True:
            r=await c.get(API+"/getUpdates",params={"offset":offset,"timeout":30})
            for u in r.json().get("result",[]): offset=u["update_id"]+1; await handle_update(u)
if __name__=="__main__": asyncio.run(main())
