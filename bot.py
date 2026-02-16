import os
import zipfile
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from scraper import buscar_manga, listar_capitulos, pegar_paginas

# =========================
# 🔐 Variáveis do Railway
# =========================
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

# =========================
# 🤖 Inicializar Bot
# =========================
app = Client(
    "manga_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token
)


# =========================
# ⚡ Download paralelo controlado
# =========================
async def baixar_imagens(urls, pasta, status_msg):
    os.makedirs(pasta, exist_ok=True)

    total = len(urls)
    progresso = 0

    # Limita downloads simultâneos (evita crash no Railway)
    sem = asyncio.Semaphore(5)

    async with aiohttp.ClientSession() as session:

        async def baixar(i, url):
            nonlocal progresso

            async with sem:
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            with open(f"{pasta}/{i}.jpg", "wb") as f:
                                f.write(await resp.read())
                except:
                    pass

                progresso += 1
                barra = "█" * int((progresso / total) * 10)
                await status_msg.edit_text(
                    f"📥 Baixando páginas...\n[{barra:<10}] {progresso}/{total}"
                )

        tarefas = [baixar(i, url) for i, url in enumerate(urls)]
        await asyncio.gather(*tarefas)


# =========================
# 📦 Criar arquivo CBZ
# =========================
def criar_cbz(pasta, nome_cbz):
    with zipfile.ZipFile(nome_cbz, "w") as z:
        arquivos = sorted(
            os.listdir(pasta),
            key=lambda x: int(x.split(".")[0])
        )

        for arquivo in arquivos:
            caminho = os.path.join(pasta, arquivo)
            z.write(caminho, arquivo)


# =========================
# 📌 Comando /start
# =========================
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "📚 MangaBot Online!\n\nUse:\n/buscar nome_do_manga"
    )


# =========================
# 🔎 Buscar mangá
# =========================
@app.on_message(filters.command("buscar"))
async def buscar(client, message):

    if len(message.command) < 2:
        return await message.reply("Use: /buscar nome")

    nome = message.text.split(" ", 1)[1]
    resultados = buscar_manga(nome)

    if not resultados:
        return await message.reply("❌ Nada encontrado")

    botoes = [
        [InlineKeyboardButton(titulo, callback_data=f"manga_{manga_id}")]
        for titulo, manga_id in resultados
    ]

    await message.reply(
        "🔎 Resultados:",
        reply_markup=InlineKeyboardMarkup(botoes)
    )


# =========================
# 📚 Escolher mangá
# =========================
@app.on_callback_query(filters.regex("^manga_"))
async def escolher_manga(client, call):

    manga_id = call.data.split("_")[1]
    caps = listar_capitulos(manga_id)

    if not caps:
        return await call.message.edit_text("❌ Sem capítulos disponíveis")

    botoes = [
        [InlineKeyboardButton(f"Capítulo {num}", callback_data=f"cap_{cap_id}")]
        for num, cap_id in caps
    ]

    await call.message.edit_text(
        "📚 Escolha um capítulo:",
        reply_markup=InlineKeyboardMarkup(botoes)
    )


# =========================
# 📥 Baixar capítulo
# =========================
@app.on_callback_query(filters.regex("^cap_"))
async def baixar_capitulo(client, call):

    cap_id = call.data.split("_")[1]

    status = await call.message.edit_text("🔄 Preparando download...")

    try:
        urls = pegar_paginas(cap_id)

        if not urls:
            return await status.edit_text("❌ Erro ao pegar páginas")

        pasta = f"temp_{cap_id}"
        nome_cbz = f"{cap_id}.cbz"

        # 🔽 Download
        await baixar_imagens(urls, pasta, status)

        # 📦 Compactar
        await status.edit_text("📦 Compactando CBZ...")
        criar_cbz(pasta, nome_cbz)

        # 📤 Enviar
        await call.message.reply_document(nome_cbz)

        # 🧹 Limpeza
        for f in os.listdir(pasta):
            os.remove(os.path.join(pasta, f))
        os.rmdir(pasta)

        os.remove(nome_cbz)

        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ Erro: {str(e)}")


# =========================
# 🚀 Rodar Bot
# =========================
print("Bot iniciado com sucesso.")
app.run()
