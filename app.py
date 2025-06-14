import os
import requests
from flask import Flask, jsonify
from bs4 import BeautifulSoup
import logging
from fake_useragent import UserAgent

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Fake UserAgent ayarları
ua = UserAgent()

def scrape_x_trends():
    try:
        headers = {
            "User-Agent": ua.random,
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "DNT": "1"
        }

        # 1. Önce Twitter'ın mobil versiyonunu çekiyoruz (daha az bot koruması var)
        response = requests.get(
            "https://x.com/explore/tabs/trending",
            headers=headers,
            timeout=15
        )
        
        # 2. Eğer redirect olursa (login isteyebilir)
        if "login" in response.url:
            raise Exception("Login gerekiyor, cookie eklemelisiniz")

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. Güncel HTML yapısı (Haziran 2025)
        trends = []
        trend_items = soup.select('div[data-testid="trend"]')  # Trend konteynırları
        
        for item in trend_items:
            try:
                name = item.select_one('span[dir="ltr"]').text.strip()
                tweet_count = item.select_one('div[role="presentation"]').text.strip()
                trends.append({
                    "name": name,
                    "tweet_count": tweet_count
                })
            except Exception as e:
                continue

        return trends if trends else []

    except Exception as e:
        app.logger.error(f"Scraping hatası: {str(e)}")
        return []

@app.route('/')
def home():
    return jsonify({"message": "Çalışıyor!", "endpoint": "/trends"})

@app.route('/trends')
def get_trends():
    trends = scrape_x_trends()
    return jsonify({
        "status": "success" if trends else "error",
        "count": len(trends),
        "trends": trends
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
