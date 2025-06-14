import os
import requests
from flask import Flask, jsonify
from bs4 import BeautifulSoup
import logging
from fake_useragent import UserAgent

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
ua = UserAgent()

def get_trends():
    try:
        # Dinamik User-Agent ve özel header'lar
        headers = {
            "User-Agent": ua.random,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "DNT": "1"
        }

        # Önce sayfanın statik halini çek
        response = requests.get(
            "https://trends24.in/",
            headers=headers,
            timeout=20
        )
        response.raise_for_status()

        # JavaScript render gerekiyorsa alternatif
        if "Checking your browser" in response.text:
            raise Exception("Cloudflare challenge detected")

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # GÜNCEL 2025 SELECTORLERİ
        trends = []
        for container in soup.select('div.trend-card'):
            location = container.find('h4').get_text(strip=True) if container.find('h4') else "Global"
            
            for item in container.select('li'):
                try:
                    name = item.find('a').get_text(strip=True)
                    count = item.select_one('span.tweet-count').get_text(strip=True) if item.select_one('span.tweet-count') else "N/A"
                    url = item.find('a')['href']
                    
                    trends.append({
                        "location": location,
                        "name": name,
                        "count": count,
                        "url": f"https://twitter.com{url}" if url.startswith('/') else url
                    })
                except Exception as e:
                    continue

        return {"status": "success", "trends": trends} if trends else {"status": "empty", "message": "No trends found"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def home():
    return jsonify({"endpoints": ["/trends"]})

@app.route('/trends')
def trends():
    return jsonify(get_trends())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
