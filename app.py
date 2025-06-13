from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime
import time
import schedule
import os
import tempfile
import shutil
import uuid

# Loglama ayarları
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
    
    # Benzersiz bir geçici dizin oluştur
    unique_id = str(uuid.uuid4())  # Her çalıştırmada benzersiz bir ID
    temp_dir = os.path.join(tempfile.gettempdir(), f"chrome_{unique_id}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Selenium ayarları
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'--user-data-dir={temp_dir}')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = None
    try:
        logging.info(f"Chrome başlatılıyor, user-data-dir: {temp_dir}")
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        logging.error(f"Chrome başlatılamadı: {str(e)}")
        # Geçici dizini temizle
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logging.info(f"Geçici dizin temizlendi: {temp_dir}")
        except Exception as e:
            logging.error(f"Geçici dizin temizlenemedi: {str(e)}")
        return trends_data
    
    for url in urls:
        country = url.split('/')[-2] if 'dubai' not in url else 'dubai'
        trends_data[country] = []
        
        try:
            logging.info(f"{country} için istek gönderiliyor: {url}")
            driver.get(url)
            
            # Trend listesinin yüklenmesini bekle
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.list-container'))
            )
            html = driver.page_source
            
            # Ham HTML'yi kaydet
            html_filename = f"{country}_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logging.info(f"{country} için ham HTML kaydedildi: {html_filename}")
            
            soup = BeautifulSoup(html, 'html.parser')
            trend_containers = soup.select('.list-container')
            
            if not trend_containers:
                logging.warning(f"{country} için .list-container bulunamadı. HTML yapısını kontrol edin.")
                trend_elements = soup.select('a.trend-link')
                for trend in trend_elements:
                    trends_data[country].append({
                        'trend': trend.text.strip(),
                        'tweet_count': 'N/A',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            else:
                for container in trend_containers:
                    timestamp = container.select_one('h3.title')['data-timestamp'] if container.select_one('h3.title') else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    trend_list = container.select('ol.trend-card__list li')
                    
                    for trend in trend_list:
                        trend_name = trend.select_one('.trend-name a')
                        tweet_count = trend.select_one('.tweet-count')
                        trends_data[country].append({
                            'trend': trend_name.text.strip() if trend_name else 'N/A',
                            'tweet_count': tweet_count['data-count'] if tweet_count and tweet_count.get('data-count') else 'N/A',
                            'timestamp': timestamp
                        })
            
            logging.info(f"{country} için trendler: {json.dumps(trends_data[country], ensure_ascii=False)}")
            
        except Exception as e:
            logging.error(f"{country} için hata: {str(e)}")
        
        time.sleep(2)
    
    # Driver'ı kapat
    if driver:
        driver.quit()
        logging.info("Selenium driver kapatıldı.")
    
    # Geçici dizini temizle
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logging.info(f"Geçici dizin temizlendi: {temp_dir}")
    except Exception as e:
        logging.error(f"Geçici dizin temizlenemedi: {str(e)}")
    
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
