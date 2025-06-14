import os
import time
from datetime import datetime
from flask import Flask, jsonify
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

# Log klasörü yoksa oluştur
if not os.path.exists("logs"):
    os.makedirs("logs")

def log_trends(trends):
    """Trendleri logs/trends.log dosyasına yazar."""
    log_file = "logs/trends.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n--- {timestamp} ---\n")
        for trend in trends:
            f.write(f"{trend}\n")

def scrape_trends():
    """Trends24.in'den trendleri çeker."""
    url = "https://trends24.in/"
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        trends = []
        
        # Trendleri çek (Örnek: Türkiye için)
        trend_container = soup.find("ol", class_="trend-card__list")
        if trend_container:
            for item in trend_container.find_all("a"):
                trends.append(item.text.strip())
        
        return trends if trends else ["Trend bulunamadı."]
    
    except Exception as e:
        return [f"Hata oluştu: {str(e)}"]

@app.route("/")
def home():
    return "Twitter Trend Scraper - /trends endpoint'ini kullanın."

@app.route("/trends")
def get_trends():
    trends = scrape_trends()
    log_trends(trends)
    return jsonify({"trends": trends})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
