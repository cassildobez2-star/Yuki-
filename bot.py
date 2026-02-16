import os
import asyncio
from pyrogram import Client, filters
from pyrogram import idle

# Pega variáveis do Railway
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
bot_token = os.environ["BOT_TOKEN"]

# Cliente do bot
app = Client(
    "manga_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
    in_memory=True  # evita problemas de sessão no Railway
)

# Comando /start
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🤖 Bot funcionando corretamente!")

# Responde qualquer mensagem
@app.on_message(filters.text & ~filters.command)
async def echo(client, message):
    await message.reply(f"Você disse: {message.text}")

async def main():
    print("🚀 Iniciando bot...")
    await app.start()
    print("✅ Bot iniciado e ouvindo mensagens...")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
