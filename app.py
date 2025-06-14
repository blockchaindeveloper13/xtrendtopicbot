import os
from flask import Flask, jsonify
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

def scrape_trends():
    url = "https://trends24.in/"
    try:
        scraper = cloudscraper.create_scraper(delay=10)
        response = scraper.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        trends = []
        for card in soup.select('div.trend-card, div.trend-wrapper'):
            location = card.select_one('h4, .location').text.strip() if card.select_one('h4, .location') else "Global"
            items = [item.text.strip() for item in card.select('li, a.trend-item')[:10]]  # İlk 10 trend
            trends.append({location: items})
        
        return trends if trends else [{"error": "No trends found"}]
    
    except Exception as e:
        return [{"error": str(e)}]

@app.route('/trends')
def get_trends():
    return jsonify(scrape_trends())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
