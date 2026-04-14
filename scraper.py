import requests
from bs4 import BeautifulSoup
import json

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 修正後的選擇器：針對官網目前 news 列表的結構
    articles = soup.select('ul.p-news-list li') 
    events = []

    for item in articles:
        # 獲取標題
        title_el = item.select_one('.p-news-list__item-title')
        if not title_el: continue
        
        title = title_el.get_text(strip=True)
        
        if "開催決定" in title:
            link_el = item.select_one('a')
            link = link_el['href'] if link_el else "#"
            full_link = link if link.startswith('http') else f"https://hakoniwalily.jp{link}"
            
            # 獲取日期
            date_el = item.select_one('.p-news-list__item-date')
            date_str = date_el.get_text(strip=True).replace('.', '-') if date_el else ""
            
            events.append({
                "title": title,
                "start": date_str,
                "url": full_link,
                "allDay": True,
                "color": "#ff69b4"
            })

    # 寫入檔案
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    
    print(f"Finished! Found {len(events)} events.")

if __name__ == "__main__":
    scrape_hakolili()
