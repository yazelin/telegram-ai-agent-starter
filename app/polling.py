import asyncio, httpx
from .config import TELEGRAM_BOT_TOKEN
from .telegram import handle_update
API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def main():
    offset = 0
    async with httpx.AsyncClient(timeout=60) as c:
        while True:
            try:
                r = await c.get(API + "/getUpdates", params={"offset": offset, "timeout": 30})
                if r.status_code != 200:
                    # 429 / 5xx etc. Back off and retry instead of crashing.
                    await asyncio.sleep(3)
                    continue
                data = r.json()
                if not data.get("ok"):
                    await asyncio.sleep(3)
                    continue
            except (httpx.HTTPError, ValueError) as e:
                # Network error or non-JSON body: log, back off, keep the loop alive.
                print(f"[polling] getUpdates failed: {e!r}; retrying...")
                await asyncio.sleep(3)
                continue
            for u in data.get("result", []):
                offset = u["update_id"] + 1
                await handle_update(u)


if __name__ == "__main__":
    asyncio.run(main())
