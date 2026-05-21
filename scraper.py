import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

SECTIONS = [
    'https://www.bola.com/',
    'https://www.bola.com/indonesia',
    'https://www.bola.com/inggris',
    'https://www.bola.com/dunia',
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; RSSBot/1.0)'}

def scrape(url):
    res = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(res.text, 'html.parser')
    items = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/read/' not in href:
            continue
        link = href if href.startswith('http') else 'https://www.bola.com' + href
        title = a.get('title') or a.get_text(strip=True)
        if title and link and not any(i['link'] == link for i in items):
            items.append({'title': title, 'link': link})
    return items

def escape(s):
    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

all_items = []
seen = set()
for url in SECTIONS:
    try:
        for item in scrape(url):
            if item['link'] not in seen:
                seen.add(item['link'])
                all_items.append(item)
        print(f"OK: {url}")
    except Exception as e:
        print(f"Error: {url} - {e}")

all_items = all_items[:20]
now = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')

xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Bola.com - Berita Terkini</title>
    <link>https://www.bola.com</link>
    <description>Berita sepak bola terkini</description>
    <language>id</language>
    <lastBuildDate>{now}</lastBuildDate>
'''
for item in all_items:
    xml += f'''    <item>
      <title>{escape(item["title"])}</title>
      <link>{escape(item["link"])}</link>
      <guid>{escape(item["link"])}</guid>
    </item>
'''
xml += '  </channel>\n</rss>'

with open('feed.xml', 'w', encoding='utf-8') as f:
    f.write(xml)

print(f"Selesai! {len(all_items)} artikel ditemukan.")
