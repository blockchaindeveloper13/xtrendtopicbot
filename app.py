import os
import logging
from datetime import datetime
from flask import Flask, jsonify
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

# Heroku-friendly log ayarları
logging.basicConfig(level=logging.INFO)
app.logger.addHandler(logging.StreamHandler())

def scrape_trends():
    """Trendleri çekip hem JSON hem log olarak döner"""
    url = "https://trends24.in/"
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        trends = []
        
        # Güncel HTML yapısı (2025 için güncellendi)
        for card in soup.find_all('div', class_='trend-card'):
            location = card.find('h4').text.strip()
            items = [li.text.strip() for li in card.find_all('li')]
            trends.append(f"{location}: {', '.join(items)}")
        
        return trends if trends else ["No trends found"]
    
    except Exception as e:
        app.logger.error(f"SCRAPING ERROR: {str(e)}")
        return [f"Error: {str(e)}"]

@app.route('/trends')
def get_trends():
    trends = scrape_trends()
    
    # Heroku'da real-time loglama
    for trend in trends:
        app.logger.info(f"TREND: {trend}")
    
    return jsonify({
        "status": "success",
        "trends": trends,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
