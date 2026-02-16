
import enum
import shutil
import asyncio
import re
import os
import datetime as dt
from typing import Dict, Tuple, List

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaDocument
from loguru import logger

# Plugins e conversores
from img2cbz.core import fld2cbz
from img2pdf.core import fld2pdf, fld2thumb
from img2tph.core import img2tph
from plugins import MangaClient, MangaDexClient, MangasInClient, ManganatoClient
from models.db import DB, ChapterFile, Subscription, MangaOutput
from pagination import Pagination
from plugins.client import clean
from tools.aqueue import AQueue
from tools.flood import retry_on_flood

# -----------------------------
# Variáveis de ambiente (Railway)
# -----------------------------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# -----------------------------
# Cache
# -----------------------------
cache_dir = "/tmp/cache"
os.makedirs(cache_dir, exist_ok=True)

# -----------------------------
# Estruturas globais
# -----------------------------
mangas: Dict[str, MangaClient] = dict()
chapters: Dict[str, MangaClient] = dict()
queries: Dict[str, Tuple[MangaClient, str]] = dict()
paginations: Dict[int, Pagination] = dict()
full_pages: Dict[str, List[str]] = dict()
favourites: Dict[str, MangaClient] = dict()
locks: Dict[int, asyncio.Lock] = dict()
language_query: Dict[str, Tuple[str, str]] = dict()
pdf_queue = AQueue()
users_lock = asyncio.Lock()

# -----------------------------
# Plugins PT-BR
# -----------------------------
plugin_dicts: Dict[str, Dict[str, MangaClient]] = {
    "🇧🇷 PT": {
        "MangaDex": MangaDexClient(language=("pt-br", "pt")),
        "MangasIn": MangasInClient(language='pt'),
        "Manganato": ManganatoClient(language='pt'),
    }
}

plugins = {f"[🇧🇷 PT] {name}": plugin for name, plugin in plugin_dicts["🇧🇷 PT"].items()}

# -----------------------------
# Output Options
# -----------------------------
class OutputOptions(enum.IntEnum):
    PDF = 1
    CBZ = 2
    Telegraph = 4

    def __and__(self, other):
        return self.value & other
    def __xor__(self, other):
        return self.value ^ other
    def __or__(self, other):
        return self.value | other

def split_list(li):
    return [li[x: x + 2] for x in range(0, len(li), 2)]

def get_buttons_for_options(user_options: int):
    buttons = []
    for option in OutputOptions:
        checked = "✅" if option & user_options else "❌"
        buttons.append([InlineKeyboardButton(f"{checked} {option.name}", f"options_{option.value}")])
    return InlineKeyboardMarkup(buttons)

# -----------------------------
# Bot Client
# -----------------------------
bot = Client('bot', api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, max_concurrent_transmissions=3)

# -----------------------------
# Auxiliares
# -----------------------------
async def get_user_lock(chat_id: int):
    async with users_lock:
        lock = locks.get(chat_id)
        if not lock:
            locks[chat_id] = asyncio.Lock()
        return locks[chat_id]

# -----------------------------
# Handlers básicos
# -----------------------------
@bot.on_message(filters.command(['start']))
async def on_start(client: Client, message: Message):
    await message.reply(
        "›› **Bem-vindo ao melhor bot de mangás do Telegram!!**\n\n"
        "Digite o nome de um mangá para iniciar a busca.\n"
        "Exemplo: `Fire Force`\n\n"
        "Confira /help para mais informações."
    )

@bot.on_message(filters.command(['help']))
async def on_help(client: Client, message: Message):
    help_text = (
        "/start - Iniciar o bot\n"
        "/help - Mostrar ajuda\n"
        "/subs - Listar suas assinaturas\n"
        "/queue - Mostrar tamanho da fila\n"
        "/options - Configurar saída (PDF, CBZ, Telegraph)\n"
        "Digite o nome de um mangá para iniciar a busca."
    )
    await message.reply(help_text)

@bot.on_message(filters.command(['queue']))
async def on_queue(client: Client, message: Message):
    await message.reply(f'Tamanho da fila: {pdf_queue.qsize()}')

@bot.on_message(filters.command(['options']))
async def on_options_command(client: Client, message: Message):
    db = DB()
    user_options = await db.get(MangaOutput, str(message.from_user.id))
    user_options = user_options.output if user_options else (1 << 30) - 1
    buttons = get_buttons_for_options(user_options)
    await message.reply("Selecione o formato de saída desejado.", reply_markup=buttons)

@bot.on_message(filters.regex(r'^/'))
async def on_unknown_command(client: Client, message: Message):
    await message.reply("Comando desconhecido.")

# -----------------------------
# Pesquisa de mangás
# -----------------------------
@bot.on_message(filters.text)
async def on_message_search(client, message: Message):
    query = message.text
    for identifier, manga_client in plugin_dicts["🇧🇷 PT"].items():
        queries[f"query_PT_{identifier}_{hash(query)}"] = (manga_client, query)

    await bot.send_message(
        message.chat.id,
        "Selecione o plugin para buscar o mangá:",
        reply_markup=InlineKeyboardMarkup(
            split_list([InlineKeyboardButton(identifier, callback_data=f"query_PT_{identifier}_{hash(query)}")
                        for identifier in plugin_dicts["🇧🇷 PT"].keys()])
        )
    )

# -----------------------------
# Callbacks
# -----------------------------
@bot.on_callback_query()
async def on_callback(client, callback: CallbackQuery):
    data = callback.data
    if data.startswith("query_PT_"):
        await plugin_click(client, callback)
    elif data.startswith("options_"):
        await options_click(client, callback)
    elif data.startswith("full_page_"):
        await chapter_click(client, data, callback.from_user.id)
    else:
        await manga_click(client, callback)

# -----------------------------
# Funções de callback
# -----------------------------
async def plugin_click(client, callback: CallbackQuery):
    manga_client, query = queries[callback.data]
    results = await manga_client.search(query)
    if not results:
        await callback.message.edit("Nenhum mangá encontrado para essa pesquisa.")
        return
    for result in results:
        mangas[result.unique()] = result
    await callback.message.edit(
        "Resultados da pesquisa:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(result.name, callback_data=result.unique())] for result in results]
        )
    )

async def options_click(client, callback: CallbackQuery):
    db = DB()
    user_options = await db.get(MangaOutput, str(callback.from_user.id))
    if not user_options:
        user_options = MangaOutput(user_id=str(callback.from_user.id), output=(1 << 30) - 1)
    option = int(callback.data.split('_')[-1])
    user_options.output ^= option
    buttons = get_buttons_for_options(user_options.output)
    await db.add(user_options)
    await callback.message.edit_reply_markup(reply_markup=buttons)

async def manga_click(client, callback: CallbackQuery, pagination: Pagination = None):
    if pagination is None:
        pagination = Pagination()
        paginations[pagination.id] = pagination

    if pagination.manga is None:
        manga = mangas[callback.data]
        pagination.manga = manga

    results = await pagination.manga.client.get_chapters(pagination.manga, pagination.page)
    if not results:
        await callback.answer("Nenhum capítulo encontrado.", show_alert=True)
        return

    full_page_key = f'full_page_{hash("".join([result.unique() for result in results]))}'
    full_pages[full_page_key] = [result.unique() for result in results]
    for result in results:
        chapters[result.unique()] = result

    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton(result.name, result.unique())] for result in results] +
        [[InlineKeyboardButton("Página Completa", full_page_key)]]
    )
    await callback.message.edit_reply_markup(reply_markup=buttons)

async def chapter_click(client, data, chat_id):
    await pdf_queue.put(chapters[data], chat_id)
    logger.debug(f"Colocado capítulo {chapters[data].name} na fila do usuário {chat_id}")

# -----------------------------
# Rodar bot
# -----------------------------
if __name__ == "__main__":
    bot.run()
