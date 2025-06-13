from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime
import time
import schedule
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('trend_scraper.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(console_handler)

urls = [
    "https://trends24.in/united-arab-emirates/dubai/",
    "https://trends24.in/turkey/",
    "https://trends24.in/vietnam/",
    "https://trends24.in/saudi-arabia/",
    "https://trends24.in/brazil/",
    "https://trends24.in/india/"
]

def scrape_trends():
    trends_data = {}
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    
    for url in urls:
        country = url.split('/')[-2] if 'dubai' not in url else 'dubai'
        trends_data[country] = []
        
        try:
            logging.info(f"{country} için istek gönderiliyor: {url}")
            driver.get(url)
            time.sleep(5)  # JavaScript yüklenmesini bekle
            html = driver.page_source
            
            # Ham HTML'yi kaydet
            html_filename = f"{country}_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logging.info(f"{country} için ham HTML kaydedildi: {html_filename}")
            
            soup = BeautifulSoup(html, 'html.parser')
            trend_cards = soup.find_all('div', class_='trend-card')  # Tahmini
            
            if not trend_cards:
                logging.warning(f"{country} için trend-card bulunamadı. HTML yapısını kontrol edin.")
                trend_elements = soup.find_all('a', href=True)
                for trend in trend_elements:
                    if '#' in trend.text or trend.text.strip() in ['Netanyahu', 'Israel']:
                        trends_data[country].append({
                            'trend': trend.text.strip(),
                            'tweet_count': 'N/A',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            else:
                for card in trend_cards:
                    trend_name = card.find('a', class_='trend-link')
                    tweet_count = card.find('span', class_='trend-tweet-count')
                    if trend_name:
                        trends_data[country].append({
                            'trend': trend_name.text.strip(),
                            'tweet_count': tweet_count.text.strip() if tweet_count else 'N/A',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            logging.info(f"{country} için trendler: {json.dumps(trends_data[country], ensure_ascii=False)}")
            
        except Exception as e:
            logging.error(f"{country} için hata: {str(e)}")
        
        time.sleep(2)
    
    driver.quit()
    return trends_data

def main():
    logging.info("Trendler çekiliyor...")
    scrape_trends()
    schedule.every(90).minutes.do(scrape_trends)
    
    while True:
        schedule.run_pending()
        logging.info("Zamanlayıcı çalışıyor, bir sonraki çekim 90 dakika sonra.")
        time.sleep(60)

if __name__ == "__main__":
    main()
