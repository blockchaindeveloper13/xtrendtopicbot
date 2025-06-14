import os
import requests
from flask import Flask, jsonify
from bs4 import BeautifulSoup
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Cloudflare bypass için özel header'lar
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://trends24.in/"
}

def get_trends():
    """Trends24.in'den güncel trendleri çeker"""
    try:
        # Sayfayı çek
        response = requests.get(
            "https://trends24.in/",
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        
        # HTML'i parse et
        soup = BeautifulSoup(response.text, 'html.parser')
        trends = []
        
        # Tüm trend konteynırlarını bul
        containers = soup.find_all('div', class_='list-container')
        
        for container in containers:
            # Zaman damgasını al
            timestamp = container.find('h3', class_='title').get('data-timestamp', '')
            date_str = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
            
            # Trend öğelerini işle
            for item in container.select('ol.trend-card__list > li'):
                try:
                    name = item.find('a', class_='trend-link').text.strip()
                    count = item.find('span', class_='tweet-count').text.strip()
                    url = item.find('a', class_='trend-link')['href']
                    
                    trends.append({
                        "name": name,
                        "tweet_count": count,
                        "url": f"https://twitter.com{url}",
                        "timestamp": timestamp,
                        "date": date_str
                    })
                except Exception as e:
                    logging.warning(f"Trend parse hatası: {str(e)}")
                    continue
        
        return {
            "status": "success",
            "count": len(trends),
            "trends": trends,
            "last_updated": datetime.now().isoformat()
        }
    
    except Exception as e:
        logging.error(f"Scraping hatası: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.route('/')
def home():
    return """
    <h1>Twitter Trend Scraper</h1>
    <p>Endpoints:</p>
    <ul>
        <li><a href="/trends">/trends</a> - Tüm trendleri getir</li>
        <li><a href="/top">/top</a> - En popüler 5 trend</li>
    </ul>
    """

@app.route('/trends')
def trends():
    return jsonify(get_trends())

@app.route('/top')
def top_trends():
    data = get_trends()
    if data['status'] == 'success':
        data['trends'] = sorted(
            data['trends'],
            key=lambda x: int(x['tweet_count'].replace('K', '000').replace('M', '000000')),
            reverse=True
        )[:5]
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
