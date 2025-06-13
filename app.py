import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime
import time
import schedule

# Loglama ayarları: Hem dosyaya hem konsola yaz
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('trend_scraper.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(console_handler)

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
        country = url.split('/')[-2] if 'dubai' not in url else 'dubai'
        trends_data[country] = []
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            trend_elements = soup.find_all('div', class_='trend-name')  # HTML yapısına göre güncelle
            tweet_counts = soup.find_all('span', class_='tweet-count')  # HTML yapısına göre güncelle
            
            for trend, count in zip(trend_elements, tweet_counts):
                trend_name = trend.text.strip()
                tweet_count = count.text.strip() if count else 'N/A'
                trends_data[country].append({
                    'trend': trend_name,
                    'tweet_count': tweet_count,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            logging.info(f"{country} için trendler: {json.dumps(trends_data[country], ensure_ascii=False)}")
            
        except Exception as e:
            logging.error(f"{country} için hata: {str(e)}")
        
        time.sleep(2)
    
    return trends_data

# Ana fonksiyon
def main():
    logging.info("Trendler çekiliyor...")
    schedule.every(90).minutes.do(scrape_trends)
    
    while True:
        schedule.run_pending()
        logging.info("Zamanlayıcı çalışıyor, bir sonraki çekim 90 dakika sonra.")
        time.sleep(60)

if __name__ == "__main__":
    main()
