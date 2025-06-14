import os
import logging
from flask import Flask, jsonify
import cloudscraper
from bs4 import BeautifulSoup
import uuid

app = Flask(__name__)

# Log ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_html(html):
    """Debug için HTML kaydet"""
    filename = f"/tmp/page_{uuid.uuid4()}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    return filename

def scrape_trends():
    url = "https://trends24.in/"
    scraper = cloudscraper.create_scraper()
    
    try:
        # User-Agent ekle
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = scraper.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # HTML'i kaydet (debug)
        html_file = save_html(response.text)
        logger.info(f"HTML saved to: {html_file}")
        
        # Parse işlemi
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tüm trend kartlarını bul
        trend_cards = soup.find_all('div', class_='trend-card')
        
        if not trend_cards:
            # Alternatif selector deneyelim
            trend_cards = soup.find_all('div', class_=lambda x: x and 'trend' in x.lower())
        
        trends = []
        for card in trend_cards:
            try:
                location = card.find('h4').text.strip() if card.find('h4') else "Unknown"
                items = [li.text.strip() for li in card.find_all('li')] or \
                       [a.text.strip() for a in card.find_all('a')]
                
                trends.append({
                    "location": location,
                    "items": items
                })
            except Exception as e:
                logger.error(f"Card parse error: {str(e)}")
                continue
        
        return trends if trends else [{"error": "No trends found"}]
    
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        return [{"error": str(e)}]

@app.route('/trends')
def get_trends():
    trends = scrape_trends()
    return jsonify({
        "status": "success",
        "data": trends,
        "note": "Check Heroku logs for raw HTML files"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
