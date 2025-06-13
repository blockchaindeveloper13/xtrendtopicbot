import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime
import time

# Loglama ayarları
logging.basicConfig(
    filename='trend_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Trends24.in URL'leri
urls = [
    "https://trends24.in/united-arab-emirates/dubai/",
    "https://trends24.in/turkey/",
    "https://trends24.in/vietnam/",
    "https://trends24.in/saudi-arabia/",
    "https://trends24.in/brazil/",
    "https://trends24.in/india/"
]

# Veri çekme fonksiyonu
def scrape_trends():
    trends_data = {}
    
    for url in urls:
        # Ülke adını URL'den çıkar
        country = url.split('/')[-2] if 'dubai' not in url else 'dubai'
        trends_data[country] = []
        
        try:
            # Bot engellemesi için User-Agent
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Hata kontrolü
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trendleri bul (HTML yapısına göre güncellenmeli)
            trend_elements = soup.find_all('div', class_='trend-name')  # Örnek seçici
            tweet_counts = soup.find_all('span', class_='tweet-count')  # Tweet sayıları için tahmini
            
            # Trend ve tweet sayılarını eşleştir
            for trend, count in zip(trend_elements, tweet_counts):
                trend_name = trend.text.strip()
                tweet_count = count.text.strip() if count else 'N/A'
                trends_data[country].append({
                    'trend': trend_name,
                    'tweet_count': tweet_count,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Loglama
            logging.info(f"{country} için trendler: {json.dumps(trends_data[country], ensure_ascii=False)}")
            
        except Exception as e:
            logging.error(f"{country} için hata: {str(e)}")
        
        # İstekler arasında bekleme (bot engellemesi önlemek için)
        time.sleep(2)
    
    return trends_data

# Ana fonksiyon
def main():
    print("Trendler çekiliyor...")
    trends = scrape_trends()
    
    # Konsolda veriyi göster (test için)
    for country, trends_list in trends.items():
        print(f"\n{country} için trendler:")
        for trend in trends_list:
            print(f"  {trend['trend']} - {trend['tweet_count']}")

if __name__ == "__main__":
    main()
