from flask import Flask
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import schedule
import time
import threading
import os

app = Flask(__name__)

SITES = {
    'bola-com': {
        'name': 'Bola.com',
        'sections': [
            'https://www.bola.com/',
            'https://www.bola.com/indonesia',
            'https://www.bola.com/inggris',
            'https://www.bola.com/dunia',
        ],
        'keyword': '/read/',
        'base': 'https://www.bola.com',
    },
    'bbc-sport': {
        'name': 'BBC Sport',
        'sections': [
            'https://www.bbc.com/sport/football',
        ],
        'keyword': '/sport/football/',
        'base': 'https://www.bbc.com',
    },
    'skysports': {
        'name': 'Sky Sports Football',
        'sections': [
            'https://www.skysports.com/football',
        ],
        'keyword': '/football/',
        'base': 'https://www.skysports.com',
    },
    'telegraph': {
        'name': 'The Telegraph Football',
        'sections': [
            'https://www.telegraph.co.uk/football/',
        ],
        'keyword': '/football/',
        'base': 'https://www.telegraph.co.uk',
    },
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; RSSBot/1.0)'}

def escape(s):
    return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def scrape_site(site_id, config):
    items = []
    seen = set()
    for url in config['sections']:
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if config['keyword'] not in href:
                    continue
                link = href if href.startswith('http') else config['base'] + href
                title = a.get('title') or a.get_text(strip=True)
                if title and len(title) > 10 and link not in seen:
                    seen.add(link)
                    items.append({'title': title, 'link': link})
        except Exception as e:
            print(f"[error] {url}: {e}")
    return items[:20]

def build_rss(site_id, config, items):
    now = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(config["name"])}</title>
    <link>{config["sections"][0]}</link>
    <description>RSS feed otomatis dari {escape(config["name"])}</description>
    <language>id</language>
    <lastBuildDate>{now}</lastBuildDate>
'''
    for item in items:
        xml += f'''    <item>
      <title>{escape(item["title"])}</title>
      <link>{escape(item["link"])}</link>
      <guid>{escape(item["link"])}</guid>
    </item>
'''
    xml += '  </channel>\n</rss>'
    return xml

def run_all():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Mulai scrape semua website...")
    os.makedirs('feeds', exist_ok=True)
    for site_id, config in SITES.items():
        items = scrape_site(site_id, config)
        xml = build_rss(site_id, config, items)
        with open(f'feeds/{site_id}.xml', 'w', encoding='utf-8') as f:
            f.write(xml)
        print(f"[ok] {config['name']}: {len(items)} artikel")
    print("Selesai!\n")

# Route untuk cek status
@app.route('/')
def index():
    return '<h2>RSS Scraper aktif!</h2><p>Feed tersedia di /feed/bola-com, /feed/bbc-sport, /feed/skysports, /feed/telegraph</p>'

@app.route('/feed/<site_id>')
def feed(site_id):
    path = f'feeds/{site_id}.xml'
    if not os.path.exists(path):
        return 'Feed belum tersedia', 404
    with open(path, encoding='utf-8') as f:
        content = f.read()
    return content, 200, {'Content-Type': 'application/rss+xml'}

@app.route('/run')
def manual_run():
    run_all()
    return 'Scrape selesai!'

# Jadwal otomatis setiap 30 menit
schedule.every(30).minutes.do(run_all)

def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Jalankan scraper pertama kali saat startup
run_all()

# Jalankan scheduler di background
t = threading.Thread(target=scheduler, daemon=True)
t.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
