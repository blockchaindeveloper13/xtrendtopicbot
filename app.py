import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime
import time
import schedule
import os

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
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            logging.info(f"{country} için istek gönderiliyor: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Ham HTML'yi dosyaya kaydet
            html_filename = f"{country}_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logging.info(f"{country} için ham HTML kaydedildi: {html_filename}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Daha genel bir seçici dene (örneğin, trend-card sınıfı içeren div'ler)
            trend_cards = soup.find_all('div', class_='trend-card')  # Tahmini
            if not trend_cards:
                logging.warning(f"{country} için trend-card bulunamadı. HTML yapısını kontrol edin.")
                # Alternatif: Tüm 'a' etiketlerini tara
                trend_elements = soup.find_all('a', href=True)
                for trend in trend_elements:
                    if '#' in trend.text or trend.text.strip() in ['Netanyahu', 'Israel']:  # Örnek filtre
                        trends_data[country].append({
                            'trend': trend.text.strip(),
                            'tweet_count': 'N/A',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            else:
                for card in trend_cards:
                    trend_name = card.find('a', class_='trend-link')  # Tahmini
                    tweet_count = card.find('span', class_='trend-tweet-count')  # Tahmini
                    if trend_name:
                        trends_data[country].append({
                            'trend': trend_name.text.strip(),
                            'tweet_count': tweet_count.text.strip() if tweet_count else 'N/A',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H%M%S')
                        })
            
            logging.info(f"{country} için trendler: {json.dumps(trends_data[country], ensure_ascii=False)}")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"{country} için istek hatası: {str(e)}")
        except Exception as e:
            logging.error(f"{country} için genel hata: {str(e)}")
        
        time.sleep(2)
    
    return trends_data

# Ana fonksiyon
def main():
    logging.info("Trendler çekiliyor...")
    scrape_trends()  # İlk çalıştırmada hemen çek
    schedule.every(90).minutes.do(scrape_trends)
    
    while True:
        schedule.run_pending()
        logging.info("Zamanlayıcı çalışıyor, bir sonraki çekim 90 dakika sonra.")
        time.sleep(60)

if __name__ == "__main__":
    main()
