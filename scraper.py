import requests
from bs4 import BeautifulSoup
import json

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 這裡的選擇器改為抓取所有新聞項目
    articles = soup.select('ul.p-news-list li') 
    new_events = []

    for item in articles:
        title_el = item.select_one('.p-news-list__item-title')
        if not title_el: continue
        title = title_el.get_text(strip=True)
        
        # 放寬關鍵字
        keywords = ["開催決定", "LIVE", "イベント", "出演"]
        if any(k in title for k in keywords):
            link_el = item.select_one('a')
            link = link_el['href'] if link_el else "#"
            full_link = link if link.startswith('http') else f"https://hakoniwalily.jp{link}"
            
            date_el = item.select_one('.p-news-list__item-date')
            date_str = date_el.get_text(strip=True).replace('.', '-') if date_el else ""
            
            new_events.append({
                "title": title,
                "start": date_str,
                "url": full_link,
                "allDay": True,
                "source": "auto" # 標記為自動抓取
            })

    # --- 讀取舊的手動資料並合併 ---
    try:
        with open('events.json', 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            # 保留手動輸入的資料 (source == "manual")
            manual_events = [e for e in old_data if e.get("source") == "manual"]
    except:
        manual_events = []

    # 合併後存檔
    final_events = new_events + manual_events
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(final_events, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scrape_hakolili()

var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    locale: 'zh-tw',
    // 同時讀取兩個 JSON 來源
    eventSources: [
        {
            url: 'events.json', // 自動抓取的
            color: '#ff69b4'
        },
        {
            url: 'manual_events.json', // 你手動編輯的
            color: '#6495ED'
        }
    ],
    eventClick: function(info) {
        info.jsEvent.preventDefault();
        if (info.event.url && info.event.url !== "#") {
            window.open(info.event.url, "_blank");
        }
    }
});
