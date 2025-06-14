import os
import time
from datetime import datetime
from flask import Flask, jsonify
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

# Log dosyası yolu (Heroku'da /tmp/ kullanılabilir)
LOG_DIR = "/tmp/logs"  # Heroku'da geçici dizin
LOG_FILE = os.path.join(LOG_DIR, "trends.log")

# Log klasörü yoksa oluştur
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def log_trends(trends):
    """Trendleri log dosyasına yazar."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n\n--- {timestamp} ---\n")
            for trend in trends:
                f.write(f"{trend}\n")
        app.logger.info("Log yazıldı")  # Heroku loglarına debug bilgisi
    except Exception as e:
        app.logger.error(f"Log yazma hatası: {str(e)}")

def scrape_trends():
    """Trends24.in'den trendleri çeker."""
    url = "https://trends24.in/"
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        trends = []
        
        # Örnek: Türkiye trendleri (HTML yapısı değişmiş olabilir)
        trend_container = soup.find("ol", class_="trend-card__list")
        if trend_container:
            trends = [item.text.strip() for item in trend_container.find_all("a")]
        return trends if trends else ["Trend bulunamadı."]
    except Exception as e:
        app.logger.error(f"Scraping hatası: {str(e)}")
        return [f"Hata: {str(e)}"]

@app.route("/")
def home():
    return "Twitter Trend Scraper - /trends endpoint'ini kullanın."

@app.route("/trends")
def get_trends():
    trends = scrape_trends()
    log_trends(trends)
    return jsonify({"trends": trends, "log_status": "success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
