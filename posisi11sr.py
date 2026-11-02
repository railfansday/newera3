import sqlite3
import os
from pathlib import Path
from datetime import datetime

# ==========================================================================
# KONFIGURASI PATH (PORTABEL UNTUK LINUX/GITHUB ACTIONS)
# ==========================================================================
BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = str(BASE_DIR / "database_hasil5" / "database.sqlite")
OUTPUT_FILE = str(BASE_DIR / "index.html")
OUTPUT_DIR = str(BASE_DIR)

# ⚠️ GANTI DENGAN URL GITHUB PAGES ANDA (Sesuaikan dengan repo: newera)
BASE_URL = "https://railfansday.github.io/newera"

def generate_sitemap(rows):
    sitemap_path = os.path.join(OUTPUT_DIR, "sitemap.xml")
    today = datetime.now().strftime('%Y-%m-%d')

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_parts.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    xml_parts.append(f"""    <url>
        <loc>{BASE_URL}/index.html</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>""")

    for item in rows:
        artikel_id = item[0]
        xml_parts.append(f"""    <url>
        <loc>{BASE_URL}/index.html#artikel-{artikel_id}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>""")

    xml_parts.append('</urlset>')

    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_parts))

    print(f"[SELESAI] Sitemap: {sitemap_path} ({len(rows)} artikel)")

def generate_robots():
    robots_path = os.path.join(OUTPUT_DIR, "robots.txt")

    content = f"""User-agent: *
Allow: /

# Sitemap
Sitemap: {BASE_URL}/sitemap.xml

# Crawl delay
Crawl-delay: 1
"""

    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[SELESAI] Robots: {robots_path}")

def export_to_single_html():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database tidak ditemukan di {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, judul, konten FROM artikel")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("Tidak ada artikel di dalam database.")
        return

    sample_titles = ", ".join([row[1] for row in rows[:5]]) if rows else "Berita Terkini"
    sample_titles = sample_titles[:150]

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <meta name="googlebot" content="index, follow">
    <meta name="bingbot" content="index, follow">

    <title>Kumpulan Berita & Artikel Terkini Hari Ini ({len(rows)} Update Pilihan)</title>
    <meta name="description" content="Portal berita terlengkap menyajikan update informasi seputar {sample_titles} dan berita pilihan terpopuler hari ini.">
    <meta name="keywords" content="berita terkini, info terbaru, update harian, berita Indonesia">
    <meta name="author" content="Portal Berita Indonesia">

    <meta property="og:type" content="website">
    <meta property="og:title" content="Kumpulan Berita & Artikel Terkini Hari Ini">
    <meta property="og:description" content="Portal berita terlengkap menyajikan update informasi terbaru dan terpopuler.">
    <meta property="og:url" content="{BASE_URL}/index.html">
    <meta property="og:site_name" content="Portal Berita Indonesia">
    <meta property="og:locale" content="id_ID">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Kumpulan Berita & Artikel Terkini Hari Ini">
    <meta name="twitter:description" content="Portal berita terlengkap menyajikan update informasi terbaru dan terpopuler.">

    <meta name="google-site-verification" content="GANTI_DENGAN_KODE_GSC_ANDA">

    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <link rel="dns-prefetch" href="https://cdnjs.cloudflare.com">

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "CollectionPage",
      "name": "Kumpulan Berita & Artikel Terkini",
      "description": "Portal direktori update berita pilihan dan terpopuler.",
      "isPartOf": {{
        "@type": "WebSite",
        "name": "Portal Berita Indonesia"
      }},
      "dateModified": "{datetime.now().strftime('%Y-%m-%d')}",
      "inLanguage": "id-ID"
    }}
    </script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 20px; color: #333; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header-actions {{ text-align: center; margin-bottom: 30px; background: #fff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
        .header-actions h1 {{ font-size: 26px; color: #111; margin-top: 0; }}
        .btn-download-all {{ background-color: #27ae60; color: #ffffff; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; }}
        .btn-download-all:hover {{ background-color: #219653; }}
        .article-card {{ background: #fff; padding: 25px; margin-bottom: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); position: relative; page-break-after: always; }}
        .article-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 15px; margin-bottom: 15px; }}
        .article-card h2 {{ color: #1a0dab; margin: 0; font-size: 20px; flex-grow: 1; }}
        .btn-pdf {{ background-color: #e74c3c; color: #ffffff; border: none; padding: 8px 14px; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: bold; white-space: nowrap; }}
        .btn-pdf:hover {{ background-color: #c0392b; }}
        .article-body {{ line-height: 1.6; font-size: 16px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-actions">
            <h1>Katalog Berita & Artikel Terkini ({len(rows)} Informasi Pilihan)</h1>
            <p style="margin-bottom: 20px; color: #555;">Pusat update berita harian terlengkap, akurat, dan terstruktur dalam satu halaman.</p>
            <button class="btn-download-all" onclick="downloadAllPDF()">📚 Download Semua Artikel (PDF)</button>
        </div>

        <div id="pdf-content">
"""

    for item in rows:
        artikel_id, judul, konten = item
        safe_title = str(judul).replace('"', '').replace("'", '').replace('/', '_').replace('\\', '_')

        html_content += f"""
            <article class="article-card" id="artikel-{artikel_id}">
                <div class="article-header">
                    <h2>#{artikel_id}. {judul}</h2>
                    <button class="btn-pdf no-print" onclick="downloadSinglePDF('artikel-{artikel_id}', '{safe_title}')">📄 PDF Artikel Ini</button>
                </div>
                <div class="article-body">
                    {konten}
                </div>
            </article>
"""

    html_content += """
        </div>
    </div>

    <script>
        function downloadSinglePDF(elementId, filename) {
            const element = document.getElementById(elementId);
            const btn = element.querySelector('.btn-pdf');
            btn.style.display = 'none';
            const opt = { margin: 10, filename: filename + '.pdf', image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2, useCORS: true }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } };
            html2pdf().set(opt).from(element).save().then(() => { btn.style.display = 'inline-block'; });
        }
        function downloadAllPDF() {
            const element = document.getElementById('pdf-content');
            const buttons = document.querySelectorAll('.btn-pdf');
            buttons.forEach(btn => btn.style.display = 'none');
            const opt = { margin: 10, filename: 'Kumpulan_index_News.pdf', image: { type: 'jpeg', quality: 0.95 }, html2canvas: { scale: 1.5, useCORS: true }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } };
            html2pdf().set(opt).from(element).save().then(() => { buttons.forEach(btn => btn.style.display = 'inline-block'); });
        }
    </script>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[SELESAI] Berhasil mengeksport {len(rows)} artikel:")
    print(f" -> {OUTPUT_FILE}")

    print("\n[*] Generate sitemap.xml...")
    generate_sitemap(rows)

    print("\n[*] Generate robots.txt...")
    generate_robots()

    print("\n" + "="*50)
    print("[SELESAI] Semua file siap di-deploy!")
    print("="*50)

if __name__ == "__main__":
    export_to_single_html()