import os
from dotenv import load_dotenv
load_dotenv()
TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","")
ALLOWED_USER_IDS={int(x) for x in os.getenv("ALLOWED_USER_IDS","").replace(" ","").split(",") if x}
AI_PROVIDER=os.getenv("AI_PROVIDER","echo")
HTTP_LLM_ENDPOINT=os.getenv("HTTP_LLM_ENDPOINT","")
HTTP_LLM_API_KEY=os.getenv("HTTP_LLM_API_KEY","")
MODEL_NAME=os.getenv("MODEL_NAME","gpt-4o-mini")
