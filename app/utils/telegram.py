import httpx
import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def enviar_mensaje_telegram(chat_id: str, mensaje: str):
    if not TELEGRAM_BOT_TOKEN:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    async with httpx.AsyncClient() as client:
        await client.post(url, data={
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "HTML"
        })
