import aiohttp
from bs4 import BeautifulSoup

# ========================
# Funções genéricas
# ========================

async def search(query, site_url):
    if "mangadex" in site_url:
        return await _search_mangadex(query)
    elif "slimeread" in site_url:
        return await _search_slimeread(query)
    elif "mangalivre" in site_url:
        return await _search_mangalivre(query)
    elif "manhwa18" in site_url:
        return await _search_manhwa18(query)
    elif "manhwahentai" in site_url:
        return await _search_manhwahentai(query)
    return []

async def get_chapters(manga_url):
    if "mangadex" in manga_url:
        return await _chapters_mangadex(manga_url)
    elif "slimeread" in manga_url:
        return await _chapters_slimeread(manga_url)
    elif "mangalivre" in manga_url:
        return await _chapters_mangalivre(manga_url)
    elif "manhwa18" in manga_url:
        return await _chapters_manhwa18(manga_url)
    elif "manhwahentai" in manga_url:
        return await _chapters_manhwahentai(manga_url)
    return []

async def get_pages(chapter_url):
    if "mangadex" in chapter_url:
        return await _pages_mangadex(chapter_url)
    elif "slimeread" in chapter_url:
        return await _pages_slimeread(chapter_url)
    elif "mangalivre" in chapter_url:
        return await _pages_mangalivre(chapter_url)
    elif "manhwa18" in chapter_url:
        return await _pages_manhwa18(chapter_url)
    elif "manhwahentai" in chapter_url:
        return await _pages_manhwahentai(chapter_url)
    return []

# ========================
# Implementação específica de cada site
# ========================

# Mangadex
async def _search_mangadex(query):
    url = f"https://mangadex.com/titles?title={query.replace(' ','+')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.select(".card-title a")[:10]:
        results.append({"title": item.text.strip(), "url": item["href"]})
    return results

async def _chapters_mangadex(manga_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(manga_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    chapters = []
    for chap in soup.select(".chapter-list a"):
        chapters.append({'title': chap.text.strip(), 'url': chap['href']})
    return chapters

async def _pages_mangadex(chapter_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(chapter_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    pages = [img["src"] for img in soup.select(".reader-container img")]
    return pages

# Slimeread
async def _search_slimeread(query):
    url = f"https://slimeread.com/search?keyword={query.replace(' ','+')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.select(".manga-item")[:10]:
        results.append({"title": item.select_one("h3").text.strip(),
                        "url": item.select_one("a")["href"]})
    return results

async def _chapters_slimeread(manga_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(manga_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    chapters = []
    for chap in soup.select(".chapter-list li"):
        chapters.append({'title': chap.text.strip(), 'url': chap.select_one("a")["href"]})
    return chapters

async def _pages_slimeread(chapter_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(chapter_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    pages = [img["src"] for img in soup.select(".reader img")]
    return pages

# MangaLivre
async def _search_mangalivre(query):
    url = f"https://mangalivre.net/pesquisa?q={query.replace(' ','+')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.select(".seriesList li")[:10]:
        title = item.select_one("h3").text.strip()
        link = item.select_one("a")["href"]
        results.append({"title": title, "url": link})
    return results

async def _chapters_mangalivre(manga_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(manga_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    chapters = []
    for chap in soup.select(".list-of-chapters li"):
        chapters.append({'title': chap.text.strip(), 'url': chap.select_one("a")["href"]})
    return chapters

async def _pages_mangalivre(chapter_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(chapter_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    pages = [img["src"] for img in soup.select(".container-chapter-reader img")]
    return pages

# Manhwa18
async def _search_manhwa18(query):
    url = f"https://manhwa18.com/search?query={query.replace(' ','+')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.select(".manga-title a")[:10]:
        results.append({"title": item.text.strip(), "url": item["href"]})
    return results

async def _chapters_manhwa18(manga_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(manga_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    chapters = []
    for chap in soup.select(".chapter-list li"):
        chapters.append({'title': chap.text.strip(), 'url': chap.select_one("a")["href"]})
    return chapters

async def _pages_manhwa18(chapter_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(chapter_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    pages = [img["src"] for img in soup.select(".reader-container img")]
    return pages

# Manhwahentai
async def _search_manhwahentai(query):
    url = f"https://manhwahentai.net/search?keyword={query.replace(' ','+')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.select(".manga-item a")[:10]:
        results.append({"title": item.text.strip(), "url": item["href"]})
    return results

async def _chapters_manhwahentai(manga_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(manga_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    chapters = []
    for chap in soup.select(".chapter-list li"):
        chapters.append({'title': chap.text.strip(), 'url': chap.select_one("a")["href"]})
    return chapters

async def _pages_manhwahentai(chapter_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(chapter_url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "html.parser")
    pages = [img["src"] for img in soup.select(".reader-container img")]
    return pages
