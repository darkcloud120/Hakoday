import requests
from bs4 import BeautifulSoup
import json
import re

def clean_event_title(text):
    if not text: return ""
    text = text.replace('NEWSEVENT', '').replace('{NEWS}{EVENT}', '').replace('開催決定', '').replace('！', '')
    text = re.sub(r'\d{1,4}[\.\/\-]\d{1,2}[\.\/\-]\d{1,4}', '', text)
    text = re.sub(r'^\d{1,2}[\.\/\-]\d{1,2}\s*', '', text)
    text = re.sub(r'\s*\d{1,2}[\.\/\-]\d{1,2}$', '', text)
    text = re.sub(r'\d{4}', '', text)
    return text.strip()

def scrape_hakolili():
    base_url = "https://hakoniwalily.jp/news/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    events = []
    unique_urls = set()
    
    # 設定要抓取的頁數
    max_pages = 3 

    print(f"🚀 開始抓取ハコリリ官網新聞 (預計抓取 {max_pages} 頁)...")

    for page in range(1, max_pages + 1):
        url = base_url if page == 1 else f"{base_url}page/{page}/"
        print(f"📄 正在處理第 {page} 頁: {url}")
        
        try:
            res = requests.get(url, headers=headers)
            if res.status_code != 200: break
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            links = [a for a in soup.find_all('a', href=True) if '/news/post-' in a['href']]
            
            for a in links:
                full_url = a['href'] if a['href'].startswith('http') else f"https://hakoniwalily.jp{a['href']}"
                if full_url in unique_urls or "開催決定" not in a.get_text(): continue
                unique_urls.add(full_url)

                inner_res = requests.get(full_url, headers=headers)
                inner_res.encoding = 'utf-8'
                inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
                lines = [l.strip() for l in inner_soup.get_text().split('\n') if l.strip()]
                
                event_title, event_date = "", ""
                for i, line in enumerate(lines):
                    if "タイトル" in line and i + 1 < len(lines):
                        potential = lines[i+1]
                        if "▼" not in potential and "【" not in potential:
                            event_title = clean_event_title(potential)
                    if not event_date:
                        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', line)
                        if match:
                            event_date = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"

                if not event_title:
                    event_title = clean_event_title(a.get_text(strip=True))

                events.append({
                    "title": event_title,
                    "start": event_date if event_date else "2026-04-14",
                    "url": full_url,
                    "allDay": True,
                    "description": event_title 
                })
        except Exception as e:
            print(f"❌ 第 {page} 頁發生錯誤: {e}")
            break

    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    print(f"✅ 抓取完成，共存入 {len(events)} 筆資料。")

if __name__ == "__main__":
    scrape_hakolili()
