import sqlite3
import feedparser
import requests
from bs4 import BeautifulSoup
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import re

# ==========================================================================
# KONFIGURASI PATH (PORTABEL UNTUK LINUX/GITHUB ACTIONS)
# ==========================================================================
BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = str(BASE_DIR / "database_hasil5" / "database.sqlite")
RSS_FILE = str(BASE_DIR / "rss_list.txt")
OUTPUT_DIR = str(BASE_DIR)

# ⚠️ GANTI DENGAN URL GITHUB PAGES ANDA (Sesuaikan dengan repo: newera)
BASE_URL = "https://railfansday.github.io/newera" 

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

ADSTERRA_CODE = """
<div style="text-align:center; margin:20px 0;">
    <script type="text/javascript">
        atOptions = {
            'key' : 'f9e40eb3b3cd05f1038aac7b36b33ad2',
            'format' : 'iframe',
            'height' : 90,
            'width' : 728,
            'params' : {}
        };
    </script>
    <script type="text/javascript" src="https://upholdbrilliancerecast.com/f9e40eb3b3cd05f1038aac7b36b33ad2/invoke.js"></script>
</div>
"""

TRENDING_KEYWORDS = [
    "world cup", "piala dunia", "fifa", "ai", "artificial intelligence",
    "blackbox", "openai", "gasoline", "bensin", "fuel price", "harga bbm",
    "strait of hormuz", "selat hormuz", "iran", "israel", "middle east",
    "timur tengah", "election", "pemilu", "inflation", "inflasi",
    "bitcoin", "crypto", "stock market", "saham", "tech", "gadget",
    "health", "kesehatan", "covid", "vaccine", "vaksin"
]

def calculate_search_potential(title, content):
    text = (str(title) + " " + str(content)).lower()
    score = 0
    for kw in TRENDING_KEYWORDS:
        if kw in text:
            score += 1
    return score

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artikel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE,
            judul TEXT,
            konten TEXT,
            gambar TEXT,
            tanggal_publish TEXT,
            tanggal_update TEXT
        )
    """)
    cursor.execute("PRAGMA table_info(artikel)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'gambar' not in columns:
        cursor.execute("ALTER TABLE artikel ADD COLUMN gambar TEXT")
    if 'tanggal_publish' not in columns:
        cursor.execute("ALTER TABLE artikel ADD COLUMN tanggal_publish TEXT")
    if 'tanggal_update' not in columns:
        cursor.execute("ALTER TABLE artikel ADD COLUMN tanggal_update TEXT")
    conn.commit()
    conn.close()

def extract_full_content(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        if response.status_code != 200:
            return None, None, None
        soup = BeautifulSoup(response.text, 'html.parser')

        image_url = None
        og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
        if og_image and og_image.get('content'):
            image_url = og_image['content']

        tanggal = None
        for meta_prop in ['article:published_time', 'article:modified_time', 'datePublished']:
            meta = soup.find('meta', property=meta_prop) or soup.find('meta', attrs={'name': meta_prop})
            if meta and meta.get('content'):
                tanggal = meta['content']
                break

        paragraphs = soup.find_all('p')
        full_text = []
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 40 and not any(x in text.lower() for x in ['cookie', 'privacy policy', 'subscribe', 'all rights reserved', 'terms of use']):
                full_text.append(f"<p>{text}</p>")

        if not full_text:
            return None, image_url, tanggal

        return "\n".join(full_text), image_url, tanggal
    except Exception:
        return None, None, None

def process_single_feed(feed_url):
    feed_url = feed_url.strip()
    if not feed_url or feed_url.startswith("#"):
        return 0, 0

    baru = 0
    duplikat = 0

    try:
        feed = feedparser.parse(feed_url)
        conn = sqlite3.connect(DB_PATH, timeout=15)
        cursor = conn.cursor()

        for entry in feed.entries:
            link = entry.get('link', '')
            judul = entry.get('title', 'Tanpa Judul')
            if not link:
                continue

            cursor.execute("SELECT id FROM artikel WHERE link = ?", (link,))
            if cursor.fetchone():
                duplikat += 1
                continue

            full_text_html, image_url, tanggal = extract_full_content(link)

            if not full_text_html:
                summary = entry.get('summary', entry.get('description', 'Konten tidak tersedia.'))
                full_text_html = f"<p>{summary}</p>"

            if not tanggal:
                published_parsed = entry.get('published_parsed')
                if published_parsed:
                    tanggal = datetime(*published_parsed[:6]).isoformat()
                else:
                    tanggal = datetime.now().isoformat()

            tanggal_update = datetime.now().isoformat()

            img_tag = f'<div style="text-align:center; margin-bottom:20px;"><img src="{image_url}" alt="{judul}" style="max-width:100%; height:auto; border-radius:8px;" loading="lazy"></div>' if image_url else ""

            konten_lengkap = f"""
            {img_tag}
            {ADSTERRA_CODE}
            <div class="article-body" style="font-size: 16px; line-height: 1.8; color: #333;">
                {full_text_html}
                <p style="margin-top: 25px;">
                    <a href="{link}" target="_blank" rel="nofollow noopener" style="color: #0d6efd; text-decoration: none; font-weight: bold;">
                        &rarr; Baca artikel asli
                    </a>
                </p>
            </div>
            {ADSTERRA_CODE}
            """

            try:
                cursor.execute(
                    "INSERT INTO artikel (link, judul, konten, gambar, tanggal_publish, tanggal_update) VALUES (?, ?, ?, ?, ?, ?)",
                    (link, judul, konten_lengkap, image_url, tanggal, tanggal_update)
                )
                conn.commit()
                baru += 1
            except sqlite3.IntegrityError:
                duplikat += 1
            except Exception:
                pass

        conn.close()
    except Exception as e:
        print(f"Error pada feed {feed_url}: {e}")

    return baru, duplikat

def scrape_massive_rss():
    if not os.path.exists(RSS_FILE):
        print(f"[ERROR] File {RSS_FILE} tidak ditemukan!")
        return
    init_db()
    with open(RSS_FILE, "r", encoding="utf-8") as f:
        rss_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    print(f"[*] Memulai penarikan data dari {len(rss_urls)} sumber RSS...\n")
    total_baru = 0
    total_duplikat = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_single_feed, url): url for url in rss_urls}
        for future in as_completed(futures):
            b, d = future.result()
            total_baru += b
            total_duplikat += d
    print("\n" + "="*45)
    print(f"[SELESAI PEMANENAN]")
    print(f" - Berhasil disimpan (Artikel Baru) : {total_baru}")
    print(f" - Dilewati (Sudah ada di DB)        : {total_duplikat}")
    print("="*45)

if __name__ == "__main__":
    scrape_massive_rss()