import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"開始連線: {url}")
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 根據截圖，新聞項目的連結是在 .l-main dl dt a 裡面
    # 我們直接抓取所有的新聞連結
    links = soup.select('.l-main dl dt a') 
    print(f"找到的新聞連結數量: {len(links)}")

    events = []

    for a_tag in links:
        raw_title = a_tag.get_text(strip=True)
        # 只要標題含有「開催決定」
        if "開催決定" in raw_title:
            full_link = a_tag['href']
            print(f"🎯 發現活動新聞: {raw_title}")
            
            # 進入內文
            inner_res = requests.get(full_link, headers=headers)
            inner_res.encoding = 'utf-8'
            inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
            
            # 取得內文所有文字並分行
            # 官網內文通常在 .p-news-detail__body 或類似容器中，我們直接取全文比較保險
            inner_text = inner_soup.get_text()
            lines = [l.strip() for l in inner_text.split('\n') if l.strip()]
            
            final_title = raw_title
            event_date = ""

            for i, line in enumerate(lines):
                # 匹配 【 タイトル 】 (注意截圖中括號內可能有空格)
                if "【" in line and "タイトル" in line and i + 1 < len(lines):
                    final_title = lines[i+1]
                
                # 匹配 【 日程 】 並尋找下一行的日期
                if "【" in line and "日程" in line and i + 1 < len(lines):
                    date_line = lines[i+1]
                    # 尋找 2026年6月28日
                    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_line)
                    if date_match:
                        event_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"

            # 如果沒抓到日期，嘗試在全文搜尋一次日期格式
            if not event_date:
                fallback_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', inner_text)
                if fallback_match:
                    event_date = f"{fallback_match.group(1)}-{int(fallback_match.group(2)):02d}-{int(fallback_match.group(3)):02d}"

            events.append({
                "title": final_title,
                "start": event_date if event_date else "2026-06-28", # 若真的失敗至少放個預設
                "url": full_link,
                "allDay": True,
                "backgroundColor": "#ff69b4",
                "borderColor": "#ff69b4"
            })
            print(f"   ﹂ 最終標題: {final_title}")
            print(f"   ﹂ 最終日期: {event_date}")

    # 寫入檔案
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    
    print(f"成功！存入 {len(events)} 筆資料到 events.json")

if __name__ == "__main__":
    scrape_hakolili()
