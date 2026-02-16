import os
import asyncio
from pyrogram import Client, filters
from pyrogram import idle

# Função para pegar variáveis de ambiente com validação
def get_env_var(key, required=True, convert_int=False):
    value = os.environ.get(key)
    if value is None:
        print(f"❌ Variável de ambiente {key} não encontrada!")
        if required:
            raise SystemExit(f"Defina a variável {key} no Railway e redeploy")
        else:
            return None
    if convert_int:
        try:
            value = int(value)
        except ValueError:
            print(f"❌ {key} precisa ser um número válido, atualize no Railway")
            raise SystemExit(f"{key} inválido")
    return value

# Pegando as variáveis
api_id = get_env_var("API_ID", convert_int=True)
api_hash = get_env_var("API_HASH")
bot_token = get_env_var("BOT_TOKEN")

# Cria o cliente do bot
app = Client(
    "manga_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
    in_memory=True  # importante para Railway
)

# /start
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🤖 Bot funcionando corretamente!")

# Responde qualquer mensagem
@app.on_message(filters.text & ~filters.command)
async def echo(client, message):
    await message.reply(f"Você disse: {message.text}")

# Função principal
async def main():
    print("🚀 Iniciando bot...")
    await app.start()
    print("✅ Bot iniciado e ouvindo mensagens...")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
