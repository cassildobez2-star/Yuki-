import os
import zipfile
import asyncio
import aiohttp

async def baixar_imagens(urls, pasta, status_msg=None):
    os.makedirs(pasta, exist_ok=True)
    total = len(urls)
    progresso = 0
    sem = asyncio.Semaphore(5)  # limita simultâneo

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
                if status_msg:
                    barra = "█" * int((progresso / total) * 10)
                    await status_msg.edit_text(f"📥 Baixando páginas...\n[{barra:<10}] {progresso}/{total}")

        tarefas = [baixar(i, url) for i, url in enumerate(urls)]
        await asyncio.gather(*tarefas)

def criar_cbz(pasta, nome_cbz):
    with zipfile.ZipFile(nome_cbz, "w") as z:
        arquivos = sorted(os.listdir(pasta), key=lambda x: int(x.split(".")[0]))
        for arquivo in arquivos:
            z.write(os.path.join(pasta, arquivo), arquivo)
