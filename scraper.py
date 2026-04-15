import requests
from bs4 import BeautifulSoup
import json
import os
import time

def scrape_article_image(article_url):
    """強化版：點進新聞內頁抓取真正的活動大圖"""
    try:
        # 有禮貌的爬蟲，避免被官網封鎖
        time.sleep(1.5) 
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(article_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. 優先找文章內部的第一張圖
        # 針對 WP 常見的內文區塊進行搜尋
        content_area = soup.select_one(".post-content") or \
                       soup.select_one(".entry-content") or \
                       soup.select_one("article")
        
        if content_area:
            imgs = content_area.find_all("img")
            for img in imgs:
                src = img.get("src") or img.get("data-src") # 有些圖會用懶加載
                if src:
                    # 過濾掉太小的圖片或特定關鍵字（如頭像、icon）
                    if any(x in src.lower() for x in ["icon", "logo", "avatar", "sns"]):
                        continue
                    
                    # 補全網址
                    if src.startswith("/"):
                        return "https://hakoniwalily.jp" + src
                    return src

        # 2. 如果內文沒圖，嘗試找主題圖 (Featured Image)
        featured = soup.select_one(".post-thumbnail img") or soup.select_one(".wp-post-image")
        if featured and featured.get("src"):
            src = featured["src"]
            return "https://hakoniwalily.jp" + src if src.startswith("/") else src

    except Exception as e:
        print(f"抓取內頁圖片失敗 ({article_url}): {e}")
    return None

def scrape_hakoniwalily():
    url = "https://hakoniwalily.jp/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 修正：針對官網新聞列表的標籤選擇器
        # 假設結構是 <article> 裡面的 <a>
        articles = soup.select("article")
        new_events = []

        for article in articles:
            date_raw = article.select_one(".date")
            title_raw = article.select_one(".title")
            link_raw = article.select_one("a")

            if date_raw and title_raw:
                date_str = date_raw.get_text(strip=True).replace(".", "-")
                title_str = title_raw.get_text(strip=True)
                link_url = link_raw["href"] if link_raw else "https://hakoniwalily.jp/news/"

                # 只有當網址是官網內頁時才抓圖
                image_url = None
                if "hakoniwalily.jp" in link_url and "/news/" in link_url:
                    print(f"正在分析: {title_str}...")
                    image_url = scrape_article_image(link_url)

                new_events.append({
                    "title": title_str,
                    "start": date_str,
                    "url": link_url,
                    "description": title_str,
                    "image": image_url
                })

        return new_events
    except Exception as e:
        print(f"列表抓取失敗: {e}")
        return []

def save_and_merge_events(new_events):
    file_name = 'events.json'
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
        except: existing_events = []
    else: existing_events = []

    # 建立識別集
    existing_ids = {f"{ev['title']}_{ev['start']}" for ev in existing_events}

    added_count = 0
    updated_count = 0
    for event in new_events:
        event_id = f"{event['title']}_{event['start']}"
        if event_id not in existing_ids:
            existing_events.append(event)
            added_count += 1
        else:
            # 💡 關鍵修正：如果舊活動沒圖片但新抓的有，就補上去
            for ex_ev in existing_events:
                if f"{ex_ev['title']}_{ex_ev['start']}" == event_id:
                    if not ex_ev.get("image") and event.get("image"):
                        ex_ev["image"] = event["image"]
                        updated_count += 1

    # 按日期降序排列
    existing_events.sort(key=lambda x: x['start'], reverse=True)

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(existing_events, f, ensure_ascii=False, indent=2)
    
    print(f"任務完成！新增: {added_count}, 更新圖片: {updated_count}")

if __name__ == "__main__":
    latest_news = scrape_hakoniwalily()
    if latest_news:
        save_and_merge_events(latest_news)
