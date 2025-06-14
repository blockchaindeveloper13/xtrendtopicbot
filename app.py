import os
import logging
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

# Log ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def scrape_with_selenium():
    driver = None
    try:
        driver = get_driver()
        driver.get("https://trends24.in/")
        
        # Sayfanın yüklenmesini bekle
        time.sleep(5)
        
        # Sayfa kaynağını al
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Güncel trendleri bul (2025 HTML yapısı)
        trends = []
        trend_cards = soup.find_all('div', class_='trend-card')
        
        for card in trend_cards:
            location = card.find('h4').text.strip() if card.find('h4') else "Global"
            items = [li.text.strip() for li in card.find_all('li')] or \
                   [a.text.strip() for a in card.find_all('a', class_='trend-item')]
            
            trends.append({
                "location": location,
                "items": items[:10]  # İlk 10 trend
            })
        
        return trends if trends else [{"error": "No trends found"}]
    
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        return [{"error": str(e)}]
    
    finally:
        if driver:
            driver.quit()

@app.route('/trends')
def get_trends():
    return jsonify({
        "status": "success",
        "data": scrape_with_selenium()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
